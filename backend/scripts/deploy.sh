#!/bin/bash

# ================================================================
# Blue-Green Deployment Script for Atalaia Tintas Paint Store System
# ================================================================
#
# This script implements zero-downtime deployments using blue-green strategy
# for the paint store system, ensuring continuous availability during updates.
#
# Features:
# - Zero-downtime deployment with health checks
# - Automatic rollback on failure
# - Database migration handling  
# - Static file collection and optimization
# - Service dependency management
# - Comprehensive logging and monitoring
# - Safety checks and validations
#
# Usage:
#   ./deploy.sh [--env=ENV] [--rollback] [--force] [--dry-run]
#
# Author: Atalaia Tintas DevOps Team
# Version: 1.0.0

set -euo pipefail

# ================================
# Configuration and Constants
# ================================

# Script metadata
SCRIPT_NAME="$(basename "$0")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
BACKEND_DIR="$PROJECT_ROOT/backend"

# Default configuration
DEFAULT_ENV="production"
DEFAULT_NOTIFICATION_EMAIL="admin@atalaiastintas.com"
DEFAULT_SLACK_WEBHOOK=""

# Deployment settings
DEPLOYMENT_USER="${DEPLOYMENT_USER:-tintas}"
DEPLOYMENT_GROUP="${DEPLOYMENT_GROUP:-tintas}"
HEALTH_CHECK_TIMEOUT=300  # 5 minutes
HEALTH_CHECK_INTERVAL=10  # 10 seconds
ROLLBACK_TIMEOUT=120      # 2 minutes
DATABASE_BACKUP_RETENTION=7  # days

# Service management
SUPERVISOR_CONFIG="/etc/supervisor/conf.d/tintas.conf"
NGINX_CONFIG="/etc/nginx/sites-available/tintas"
REDIS_CONFIG="$BACKEND_DIR/config/redis.conf"

# Current timestamp for deployment tracking
DEPLOYMENT_ID="deploy_$(date +%Y%m%d_%H%M%S)"
DEPLOYMENT_LOG="/var/log/tintas/deployments/${DEPLOYMENT_ID}.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ================================
# Utility Functions
# ================================

# Logging function with timestamp and color
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "INFO")  echo -e "${GREEN}[INFO]${NC}  [$timestamp] $message" | tee -a "$DEPLOYMENT_LOG" ;;
        "WARN")  echo -e "${YELLOW}[WARN]${NC}  [$timestamp] $message" | tee -a "$DEPLOYMENT_LOG" ;;
        "ERROR") echo -e "${RED}[ERROR]${NC} [$timestamp] $message" | tee -a "$DEPLOYMENT_LOG" ;;
        "DEBUG") echo -e "${BLUE}[DEBUG]${NC} [$timestamp] $message" | tee -a "$DEPLOYMENT_LOG" ;;
        *)       echo "[$timestamp] $message" | tee -a "$DEPLOYMENT_LOG" ;;
    esac
}

# Error handler
error_exit() {
    log "ERROR" "$1"
    cleanup_on_error
    exit 1
}

# Success handler
success_exit() {
    log "INFO" "$1"
    send_deployment_notification "SUCCESS" "$1"
    exit 0
}

# Create deployment log directory
setup_logging() {
    local log_dir="/var/log/tintas/deployments"
    mkdir -p "$log_dir"
    chown "$DEPLOYMENT_USER:$DEPLOYMENT_GROUP" "$log_dir"
    
    log "INFO" "Starting deployment $DEPLOYMENT_ID"
    log "INFO" "Deployment log: $DEPLOYMENT_LOG"
}

# Check if running as correct user
check_user() {
    if [[ $(id -un) != "$DEPLOYMENT_USER" ]] && [[ $EUID -ne 0 ]]; then
        error_exit "Script must be run as $DEPLOYMENT_USER or root"
    fi
}

# Parse command line arguments
parse_arguments() {
    ENVIRONMENT="$DEFAULT_ENV"
    ROLLBACK=false
    FORCE_DEPLOY=false
    DRY_RUN=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --env=*)
                ENVIRONMENT="${1#*=}"
                shift
                ;;
            --rollback)
                ROLLBACK=true
                shift
                ;;
            --force)
                FORCE_DEPLOY=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                error_exit "Unknown option: $1"
                ;;
        esac
    done
    
    log "INFO" "Environment: $ENVIRONMENT"
    log "INFO" "Rollback mode: $ROLLBACK"
    log "INFO" "Force deploy: $FORCE_DEPLOY"
    log "INFO" "Dry run: $DRY_RUN"
}

# Show help message
show_help() {
    cat << EOF
Atalaia Tintas Blue-Green Deployment Script

Usage: $SCRIPT_NAME [OPTIONS]

OPTIONS:
    --env=ENV        Deployment environment (default: production)
    --rollback       Perform rollback to previous version
    --force          Force deployment even if health checks fail
    --dry-run        Show what would be done without executing
    --help, -h       Show this help message

EXAMPLES:
    # Normal deployment
    ./$SCRIPT_NAME

    # Deploy to staging
    ./$SCRIPT_NAME --env=staging

    # Rollback current deployment
    ./$SCRIPT_NAME --rollback

    # Force deployment (skip some safety checks)
    ./$SCRIPT_NAME --force

    # Test deployment steps without executing
    ./$SCRIPT_NAME --dry-run

ENVIRONMENT VARIABLES:
    DEPLOYMENT_USER     User to run deployment (default: tintas)
    DEPLOYMENT_GROUP    Group to run deployment (default: tintas)
    NOTIFICATION_EMAIL  Email for deployment notifications
    SLACK_WEBHOOK      Slack webhook for deployment notifications

EOF
}

# ================================
# Environment Detection and Management
# ================================

# Get current active environment (blue or green)
get_current_environment() {
    local nginx_upstream
    
    # Check which upstream is active in nginx config
    if nginx_upstream=$(grep -o "tintas_[a-z]*" "$NGINX_CONFIG" | grep upstream | head -1); then
        echo "${nginx_upstream#tintas_}"
    else
        # Default to blue if cannot determine
        echo "blue"
    fi
}

# Get target environment (opposite of current)
get_target_environment() {
    local current_env=$1
    
    if [[ "$current_env" == "blue" ]]; then
        echo "green"
    else
        echo "blue"
    fi
}

# Validate environment setup
validate_environment() {
    local env=$1
    
    log "INFO" "Validating $env environment setup"
    
    # Check if virtual environment exists
    if [[ ! -d "$PROJECT_ROOT/venv" ]]; then
        error_exit "Python virtual environment not found at $PROJECT_ROOT/venv"
    fi
    
    # Check if Django settings exist
    local settings_file="$BACKEND_DIR/tintas_system/settings/${ENVIRONMENT}.py"
    if [[ ! -f "$settings_file" ]]; then
        error_exit "Django settings file not found: $settings_file"
    fi
    
    # Check database connectivity
    if ! check_database_connection "$env"; then
        error_exit "Database connection failed for $env environment"
    fi
    
    log "INFO" "$env environment validation successful"
}

# ================================
# Service Management
# ================================

# Check service status
check_service_status() {
    local service_name=$1
    
    if systemctl is-active --quiet "$service_name"; then
        return 0
    else
        return 1
    fi
}

# Start services for environment
start_environment_services() {
    local env=$1
    
    log "INFO" "Starting $env environment services"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "DEBUG" "[DRY RUN] Would start supervisor group: tintas_$env"
        return 0
    fi
    
    # Start supervisor group for environment
    if ! supervisorctl start "tintas_${env}:*"; then
        error_exit "Failed to start $env environment services"
    fi
    
    log "INFO" "$env environment services started"
}

# Stop services for environment  
stop_environment_services() {
    local env=$1
    
    log "INFO" "Stopping $env environment services"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "DEBUG" "[DRY RUN] Would stop supervisor group: tintas_$env"
        return 0
    fi
    
    # Stop supervisor group for environment
    if ! supervisorctl stop "tintas_${env}:*"; then
        log "WARN" "Failed to stop $env environment services gracefully"
        # Force kill if graceful stop fails
        supervisorctl stop all || true
    fi
    
    log "INFO" "$env environment services stopped"
}

# ================================
# Health Checks
# ================================

# Comprehensive health check for environment
perform_health_check() {
    local env=$1
    local timeout=${2:-$HEALTH_CHECK_TIMEOUT}
    
    log "INFO" "Performing health check for $env environment (timeout: ${timeout}s)"
    
    local start_time=$(date +%s)
    local end_time=$((start_time + timeout))
    
    while [[ $(date +%s) -lt $end_time ]]; do
        if check_application_health "$env" && \
           check_database_health "$env" && \
           check_cache_health "$env" && \
           check_celery_health "$env"; then
            
            local elapsed=$(($(date +%s) - start_time))
            log "INFO" "$env environment health check passed (${elapsed}s)"
            return 0
        fi
        
        log "DEBUG" "Health check failed, retrying in ${HEALTH_CHECK_INTERVAL}s..."
        sleep $HEALTH_CHECK_INTERVAL
    done
    
    log "ERROR" "$env environment health check failed after ${timeout}s"
    return 1
}

# Check application HTTP endpoints
check_application_health() {
    local env=$1
    local port
    
    case $env in
        "blue")  port="8000" ;;
        "green") port="8002" ;;
        *) error_exit "Invalid environment: $env" ;;
    esac
    
    # Check main health endpoint
    if curl -sf "http://127.0.0.1:$port/health/" > /dev/null 2>&1; then
        log "DEBUG" "$env application health check passed"
        return 0
    else
        log "DEBUG" "$env application health check failed"
        return 1
    fi
}

# Check database connectivity
check_database_health() {
    local env=$1
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "DEBUG" "[DRY RUN] Would check database connectivity for $env"
        return 0
    fi
    
    # Use Django management command to check database
    cd "$BACKEND_DIR"
    if DEPLOYMENT_ENV="$env" "$PROJECT_ROOT/venv/bin/python" manage.py shell -c "
from django.db import connection; 
connection.ensure_connection(); 
print('DB OK')
" > /dev/null 2>&1; then
        log "DEBUG" "$env database health check passed"
        return 0
    else
        log "DEBUG" "$env database health check failed"
        return 1
    fi
}

# Check Redis cache connectivity
check_cache_health() {
    local env=$1
    
    if redis-cli ping > /dev/null 2>&1; then
        log "DEBUG" "$env cache health check passed"
        return 0
    else
        log "DEBUG" "$env cache health check failed"  
        return 1
    fi
}

# Check Celery worker status
check_celery_health() {
    local env=$1
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "DEBUG" "[DRY RUN] Would check Celery workers for $env"
        return 0
    fi
    
    cd "$BACKEND_DIR"
    if DEPLOYMENT_ENV="$env" "$PROJECT_ROOT/venv/bin/python" -m celery --app=tintas_system.celery:app inspect active > /dev/null 2>&1; then
        log "DEBUG" "$env Celery health check passed"
        return 0
    else
        log "DEBUG" "$env Celery health check failed"
        return 1
    fi
}

# Check database connection
check_database_connection() {
    local env=$1
    
    cd "$BACKEND_DIR"
    DEPLOYMENT_ENV="$env" "$PROJECT_ROOT/venv/bin/python" manage.py check --database > /dev/null 2>&1
}

# ================================
# Database Operations
# ================================

# Create database backup before deployment
create_database_backup() {
    log "INFO" "Creating database backup before deployment"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "DEBUG" "[DRY RUN] Would create database backup"
        return 0
    fi
    
    local backup_dir="/var/backups/tintas/database"
    local backup_file="${backup_dir}/pre_deploy_${DEPLOYMENT_ID}.sql"
    
    mkdir -p "$backup_dir"
    
    # Use backup script with deployment flag
    if "$SCRIPT_DIR/backup.sh" --database --output="$backup_file" --reason="pre-deployment"; then
        log "INFO" "Database backup created: $backup_file"
        
        # Clean up old backups
        find "$backup_dir" -name "pre_deploy_*.sql" -mtime +$DATABASE_BACKUP_RETENTION -delete
    else
        error_exit "Failed to create database backup"
    fi
}

# Run database migrations
run_database_migrations() {
    local env=$1
    
    log "INFO" "Running database migrations for $env environment"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "DEBUG" "[DRY RUN] Would run database migrations"
        return 0
    fi
    
    cd "$BACKEND_DIR"
    
    # Check for pending migrations first
    if ! DEPLOYMENT_ENV="$env" "$PROJECT_ROOT/venv/bin/python" manage.py showmigrations --plan | grep -q "\[ \]"; then
        log "INFO" "No pending migrations found"
        return 0
    fi
    
    # Run migrations
    if DEPLOYMENT_ENV="$env" "$PROJECT_ROOT/venv/bin/python" manage.py migrate --noinput; then
        log "INFO" "Database migrations completed successfully"
    else  
        error_exit "Database migrations failed"
    fi
}

# ================================
# Static Files and Assets
# ================================

# Collect and optimize static files
collect_static_files() {
    local env=$1
    
    log "INFO" "Collecting static files for $env environment"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "DEBUG" "[DRY RUN] Would collect static files"
        return 0
    fi
    
    cd "$BACKEND_DIR"
    
    # Collect static files
    if DEPLOYMENT_ENV="$env" "$PROJECT_ROOT/venv/bin/python" manage.py collectstatic --noinput --clear; then
        log "INFO" "Static files collected successfully"
    else
        error_exit "Failed to collect static files"
    fi
    
    # Compress static assets if django-compressor is available
    if DEPLOYMENT_ENV="$env" "$PROJECT_ROOT/venv/bin/python" manage.py compress --force > /dev/null 2>&1; then
        log "INFO" "Static assets compressed successfully"
    else
        log "DEBUG" "Static asset compression not available or failed"
    fi
}

# ================================
# Traffic Switching
# ================================

# Switch Nginx upstream to target environment
switch_traffic() {
    local target_env=$1
    
    log "INFO" "Switching traffic to $target_env environment"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "DEBUG" "[DRY RUN] Would switch Nginx upstream to $target_env"
        return 0
    fi
    
    # Create backup of current nginx config
    cp "$NGINX_CONFIG" "${NGINX_CONFIG}.backup.${DEPLOYMENT_ID}"
    
    # Update nginx upstream configuration
    if sed -i "s/upstream tintas_active {/upstream tintas_active_old {/g" "$NGINX_CONFIG" && \
       sed -i "s/upstream tintas_${target_env} {/upstream tintas_active {/g" "$NGINX_CONFIG" && \
       sed -i "s/upstream tintas_active_old {/upstream tintas_${target_env} {/g" "$NGINX_CONFIG"; then
        
        # Test nginx configuration
        if nginx -t 2>/dev/null; then
            # Reload nginx with new configuration
            if systemctl reload nginx; then
                log "INFO" "Traffic switched to $target_env environment successfully"
            else
                # Restore backup on reload failure
                cp "${NGINX_CONFIG}.backup.${DEPLOYMENT_ID}" "$NGINX_CONFIG"
                error_exit "Failed to reload Nginx with new configuration"
            fi
        else
            # Restore backup on config test failure
            cp "${NGINX_CONFIG}.backup.${DEPLOYMENT_ID}" "$NGINX_CONFIG"
            error_exit "Nginx configuration test failed"
        fi
    else
        error_exit "Failed to update Nginx configuration"
    fi
}

# ================================
# Deployment Process
# ================================

# Main deployment function
perform_deployment() {
    local current_env
    local target_env
    
    # Get current and target environments
    current_env=$(get_current_environment)
    target_env=$(get_target_environment "$current_env")
    
    log "INFO" "Current environment: $current_env"
    log "INFO" "Target environment: $target_env"
    
    # Pre-deployment validations
    log "INFO" "Starting pre-deployment validations"
    validate_environment "$target_env"
    
    # Create database backup
    create_database_backup
    
    # Start target environment services
    start_environment_services "$target_env"
    
    # Run database migrations on target environment
    run_database_migrations "$target_env"
    
    # Collect static files for target environment  
    collect_static_files "$target_env"
    
    # Perform comprehensive health check on target environment
    if ! perform_health_check "$target_env"; then
        if [[ "$FORCE_DEPLOY" == "true" ]]; then
            log "WARN" "Health check failed but continuing due to --force flag"
        else
            # Cleanup failed deployment
            stop_environment_services "$target_env"
            error_exit "Health check failed for $target_env environment"
        fi
    fi
    
    # Switch traffic to target environment
    switch_traffic "$target_env"
    
    # Final health check after traffic switch
    if ! perform_health_check "$target_env" 30; then
        log "WARN" "Post-switch health check failed, initiating rollback"
        perform_rollback "$current_env"
        error_exit "Deployment failed, rollback completed"
    fi
    
    # Stop old environment services  
    stop_environment_services "$current_env"
    
    # Record successful deployment
    record_deployment_success "$target_env"
    
    success_exit "Deployment to $target_env environment completed successfully"
}

# Rollback to previous environment
perform_rollback() {
    local target_env=${1:-$(get_previous_environment)}
    
    log "INFO" "Starting rollback to $target_env environment"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "DEBUG" "[DRY RUN] Would perform rollback to $target_env"
        return 0
    fi
    
    # Start target environment services if not running
    if ! check_service_status "tintas_${target_env}_web"; then
        start_environment_services "$target_env" 
    fi
    
    # Health check target environment
    if perform_health_check "$target_env" $ROLLBACK_TIMEOUT; then
        # Switch traffic back
        switch_traffic "$target_env"
        
        # Final verification
        if perform_health_check "$target_env" 30; then
            log "INFO" "Rollback to $target_env environment completed successfully"
        else
            error_exit "Rollback verification failed"
        fi
    else
        error_exit "Rollback target environment health check failed"
    fi
}

# Get previous environment from deployment history
get_previous_environment() {
    local deployment_history="/var/log/tintas/deployment_history.log"
    
    if [[ -f "$deployment_history" ]]; then
        # Get last successful deployment environment  
        tail -2 "$deployment_history" | head -1 | cut -d'|' -f2 || echo "blue"
    else
        echo "blue"  # Default fallback
    fi
}

# Record deployment success
record_deployment_success() {
    local env=$1
    local deployment_history="/var/log/tintas/deployment_history.log"
    
    # Create deployment history directory
    mkdir -p "$(dirname "$deployment_history")"
    
    # Record deployment with timestamp
    echo "$(date -u '+%Y-%m-%d %H:%M:%S')|$env|$DEPLOYMENT_ID|SUCCESS" >> "$deployment_history"
    
    # Keep only last 50 deployments
    tail -50 "$deployment_history" > "${deployment_history}.tmp" && \
    mv "${deployment_history}.tmp" "$deployment_history"
}

# ================================
# Notifications
# ================================

# Send deployment notification
send_deployment_notification() {
    local status=$1
    local message=$2
    
    # Email notification
    if [[ -n "${NOTIFICATION_EMAIL:-}" ]]; then
        send_email_notification "$status" "$message"
    fi
    
    # Slack notification  
    if [[ -n "${SLACK_WEBHOOK:-}" ]]; then
        send_slack_notification "$status" "$message"
    fi
}

# Send email notification
send_email_notification() {
    local status=$1
    local message=$2
    
    local subject="[Atalaia Tintas] Deployment $status - $DEPLOYMENT_ID"
    
    cat << EOF | mail -s "$subject" "$NOTIFICATION_EMAIL" 2>/dev/null || true
Deployment Status: $status
Deployment ID: $DEPLOYMENT_ID
Environment: $ENVIRONMENT
Timestamp: $(date -u '+%Y-%m-%d %H:%M:%S UTC')

Message: $message

Log file: $DEPLOYMENT_LOG

--
Atalaia Tintas Deployment System
EOF
}

# Send Slack notification
send_slack_notification() {
    local status=$1
    local message=$2
    
    local color
    case $status in
        "SUCCESS") color="good" ;;
        "ERROR")   color="danger" ;;
        *)         color="warning" ;;
    esac
    
    local payload=$(cat << EOF
{
    "attachments": [
        {
            "color": "$color",
            "title": "Atalaia Tintas Deployment $status",
            "fields": [
                {
                    "title": "Deployment ID",
                    "value": "$DEPLOYMENT_ID",
                    "short": true
                },
                {
                    "title": "Environment", 
                    "value": "$ENVIRONMENT",
                    "short": true
                },
                {
                    "title": "Message",
                    "value": "$message",
                    "short": false
                }
            ],
            "timestamp": $(date +%s)
        }
    ]
}
EOF
    )
    
    curl -X POST -H 'Content-type: application/json' --data "$payload" "$SLACK_WEBHOOK" 2>/dev/null || true
}

# ================================
# Cleanup and Error Handling
# ================================

# Cleanup on error
cleanup_on_error() {
    log "WARN" "Cleaning up after deployment error"
    
    # Send error notification
    send_deployment_notification "ERROR" "Deployment failed during execution"
    
    # Additional cleanup steps can be added here
    # e.g., restore backups, clean temporary files, etc.
}

# Cleanup on successful exit
cleanup_on_success() {
    log "INFO" "Performing post-deployment cleanup"
    
    # Clean up old Nginx config backups (keep last 5)
    find "$(dirname "$NGINX_CONFIG")" -name "tintas.backup.*" -type f | sort -r | tail -n +6 | xargs rm -f 2>/dev/null || true
    
    # Clean up old deployment logs (keep last 30)
    find "/var/log/tintas/deployments" -name "deploy_*.log" -type f | sort -r | tail -n +31 | xargs rm -f 2>/dev/null || true
}

# ================================
# Main Script Logic
# ================================

main() {
    # Setup
    setup_logging
    check_user
    parse_arguments "$@"
    
    # Handle rollback mode
    if [[ "$ROLLBACK" == "true" ]]; then
        perform_rollback
        cleanup_on_success
        success_exit "Rollback completed successfully"
    fi
    
    # Handle normal deployment
    perform_deployment
    cleanup_on_success
}

# Trap signals for proper cleanup
trap cleanup_on_error ERR
trap cleanup_on_error INT TERM

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
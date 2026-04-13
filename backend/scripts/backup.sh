#!/bin/bash

# Backup Automation Script for Sistema de Tintas
# User Story 2: Data Integrity and Backup
# Task: T047 - Create backup automation script
#
# This script provides automated database backup functionality
# that can be scheduled via cron or run manually.
#
# Usage:
#   ./backup.sh [OPTIONS]
#   
# Options:
#   -t, --type TYPE      Backup type: full, incremental, manual (default: full)
#   -u, --user USER      Username to attribute backup to
#   -c, --cleanup        Clean up expired backups
#   -l, --list          List recent backups
#   -v, --verify ID     Verify backup integrity by ID
#   -h, --help          Show this help message
#
# Examples:
#   ./backup.sh                           # Create full backup
#   ./backup.sh -t incremental            # Create incremental backup
#   ./backup.sh -c                        # Clean up expired backups
#   ./backup.sh -l                        # List recent backups
#   ./backup.sh -v abc123                 # Verify backup with ID abc123
#   ./backup.sh -t manual -u admin        # Create manual backup attributed to admin

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MANAGE_PY="$PROJECT_DIR/manage.py"
PYTHON_CMD="${PYTHON_CMD:-python}"
LOG_FILE="${LOG_FILE:-/var/log/tintas-backup.log}"
LOCK_FILE="${LOCK_FILE:-/tmp/tintas-backup.lock}"

# Default values
BACKUP_TYPE="full"
USERNAME=""
CLEANUP=false
LIST=false
VERIFY=""
HELP=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $*" | tee -a "$LOG_FILE" >&2
}

log_warning() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [WARNING] $*" | tee -a "$LOG_FILE"
}

# Print colored output
print_success() {
    echo -e "${GREEN}✓ $*${NC}"
}

print_error() {
    echo -e "${RED}✗ $*${NC}" >&2
}

print_warning() {
    echo -e "${YELLOW}⚠ $*${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $*${NC}"
}

# Help function
show_help() {
    cat << EOF
Backup Automation Script for Sistema de Tintas

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -t, --type TYPE      Backup type: full, incremental, manual (default: full)
    -u, --user USER      Username to attribute backup to
    -c, --cleanup        Clean up expired backups
    -l, --list          List recent backups  
    -v, --verify ID     Verify backup integrity by backup ID
    -h, --help          Show this help message

EXAMPLES:
    $0                           # Create full backup
    $0 -t incremental            # Create incremental backup
    $0 -c                        # Clean up expired backups
    $0 -l                        # List recent backups
    $0 -v abc123                 # Verify backup with ID abc123
    $0 -t manual -u admin        # Create manual backup attributed to admin

ENVIRONMENT VARIABLES:
    PYTHON_CMD      Python command (default: python)
    LOG_FILE        Log file path (default: /var/log/tintas-backup.log)
    LOCK_FILE       Lock file path (default: /tmp/tintas-backup.lock)

SCHEDULING WITH CRON:
    # Full backup daily at 2 AM
    0 2 * * * /path/to/backup.sh -t full >> /var/log/tintas-backup-cron.log 2>&1

    # Incremental backup every 4 hours
    0 */4 * * * /path/to/backup.sh -t incremental >> /var/log/tintas-backup-cron.log 2>&1

    # Cleanup expired backups weekly
    0 1 * * 0 /path/to/backup.sh -c >> /var/log/tintas-backup-cron.log 2>&1

EOF
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--type)
                BACKUP_TYPE="$2"
                shift 2
                ;;
            -u|--user)
                USERNAME="$2"
                shift 2
                ;;
            -c|--cleanup)
                CLEANUP=true
                shift
                ;;
            -l|--list)
                LIST=true
                shift
                ;;
            -v|--verify)
                VERIFY="$2"
                shift 2
                ;;
            -h|--help)
                HELP=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."

    # Check if manage.py exists
    if [[ ! -f "$MANAGE_PY" ]]; then
        print_error "manage.py not found at $MANAGE_PY"
        exit 1
    fi

    # Check Python command
    if ! command -v "$PYTHON_CMD" &> /dev/null; then
        print_error "Python command '$PYTHON_CMD' not found"
        exit 1
    fi

    # Check Django settings
    if ! cd "$PROJECT_DIR" && $PYTHON_CMD "$MANAGE_PY" check --deploy --quiet; then
        print_error "Django configuration check failed"
        exit 1
    fi

    # Create log directory if it doesn't exist
    local log_dir
    log_dir="$(dirname "$LOG_FILE")"
    if [[ ! -d "$log_dir" ]]; then
        mkdir -p "$log_dir" || {
            print_error "Failed to create log directory: $log_dir"
            exit 1
        }
    fi

    print_success "Prerequisites check passed"
}

# Acquire lock to prevent concurrent executions
acquire_lock() {
    if [[ -f "$LOCK_FILE" ]]; then
        local pid
        pid="$(cat "$LOCK_FILE")"
        
        if kill -0 "$pid" 2>/dev/null; then
            print_error "Another backup process is already running (PID: $pid)"
            exit 1
        else
            print_warning "Removing stale lock file"
            rm -f "$LOCK_FILE"
        fi
    fi

    echo $$ > "$LOCK_FILE"
    trap 'rm -f "$LOCK_FILE"' EXIT
}

# Release lock
release_lock() {
    rm -f "$LOCK_FILE"
}

# Validate backup type
validate_backup_type() {
    case "$BACKUP_TYPE" in
        full|incremental|manual)
            ;;
        *)
            print_error "Invalid backup type: $BACKUP_TYPE"
            print_error "Valid types: full, incremental, manual"
            exit 1
            ;;
    esac
}

# Create backup
create_backup() {
    local cmd_args=("--type" "$BACKUP_TYPE")
    
    if [[ -n "$USERNAME" ]]; then
        cmd_args+=("--user" "$USERNAME")
    fi

    print_info "Creating $BACKUP_TYPE backup..."
    log "Starting $BACKUP_TYPE backup creation"

    if cd "$PROJECT_DIR" && $PYTHON_CMD "$MANAGE_PY" create_backup "${cmd_args[@]}"; then
        print_success "$BACKUP_TYPE backup created successfully"
        log "$BACKUP_TYPE backup created successfully"
    else
        print_error "$BACKUP_TYPE backup creation failed"
        log_error "$BACKUP_TYPE backup creation failed"
        exit 1
    fi
}

# Cleanup expired backups
cleanup_backups() {
    print_info "Cleaning up expired backups..."
    log "Starting backup cleanup"

    if cd "$PROJECT_DIR" && $PYTHON_CMD "$MANAGE_PY" create_backup --cleanup; then
        print_success "Backup cleanup completed successfully"
        log "Backup cleanup completed successfully"
    else
        print_error "Backup cleanup failed"
        log_error "Backup cleanup failed"
        exit 1
    fi
}

# List recent backups
list_backups() {
    print_info "Listing recent backups..."
    log "Listing recent backups"

    if cd "$PROJECT_DIR" && $PYTHON_CMD "$MANAGE_PY" create_backup --list; then
        log "Backup list displayed successfully"
    else
        print_error "Failed to list backups"
        log_error "Failed to list backups"
        exit 1
    fi
}

# Verify backup integrity
verify_backup() {
    print_info "Verifying backup: $VERIFY"
    log "Verifying backup: $VERIFY"

    if cd "$PROJECT_DIR" && $PYTHON_CMD "$MANAGE_PY" create_backup --verify "$VERIFY"; then
        print_success "Backup verification completed"
        log "Backup verification completed for: $VERIFY"
    else
        print_error "Backup verification failed"
        log_error "Backup verification failed for: $VERIFY"
        exit 1
    fi
}

# Main function
main() {
    # Parse command line arguments
    parse_arguments "$@"

    # Show help if requested
    if [[ "$HELP" == true ]]; then
        show_help
        exit 0
    fi

    print_info "Starting backup automation script..."
    log "Backup script started with arguments: $*"

    # Check prerequisites
    check_prerequisites

    # Acquire lock (except for list and verify operations)
    if [[ "$LIST" != true && "$VERIFY" == "" ]]; then
        acquire_lock
    fi

    # Execute requested operation
    if [[ "$CLEANUP" == true ]]; then
        cleanup_backups
    elif [[ "$LIST" == true ]]; then
        list_backups
    elif [[ -n "$VERIFY" ]]; then
        verify_backup
    else
        validate_backup_type
        create_backup
    fi

    print_success "Backup automation script completed successfully"
    log "Backup script completed successfully"
}

# Parse arguments and run main function
main "$@"
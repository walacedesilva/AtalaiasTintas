#!/bin/bash

# System Health Monitoring Script for Sistema de Tintas
# User Story 2: Data Integrity and Backup  
# Task: T048 - Create system health monitoring script
#
# This script provides comprehensive system health monitoring
# for the paint store system infrastructure.
#
# Usage:
#   ./health_check.sh [OPTIONS]
#   
# Options:
#   -c, --component COMP Component to check: database, redis, api, celery, disk, memory, cpu, all
#   -s, --summary        Show health summary for last 24 hours
#   -a, --alerts         Show active alerts
#   -r, --report HOURS   Generate health report for specified hours (default: 24)
#   -f, --format FORMAT  Output format: text, json, nagios (default: text)
#   -q, --quiet          Quiet mode - only errors and warnings
#   -v, --verbose        Verbose mode - detailed output
#   -h, --help           Show this help message
#
# Exit Codes:
#   0 - All systems healthy
#   1 - Script error or invalid arguments
#   2 - Warning conditions detected
#   3 - Critical conditions detected
#   4 - System down or unavailable
#
# Examples:
#   ./health_check.sh                     # Check all components
#   ./health_check.sh -c database         # Check only database
#   ./health_check.sh -s                  # Show summary
#   ./health_check.sh -a                  # Show active alerts
#   ./health_check.sh -f json             # JSON output
#   ./health_check.sh -r 48 -f nagios     # 48-hour report in Nagios format

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MANAGE_PY="$PROJECT_DIR/manage.py"
PYTHON_CMD="${PYTHON_CMD:-python}"
LOG_FILE="${LOG_FILE:-/var/log/tintas-health.log}"

# Default values
COMPONENT=""
SUMMARY=false
ALERTS=false
REPORT_HOURS=""
FORMAT="text"
QUIET=false
VERBOSE=false
HELP=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Exit codes
EXIT_HEALTHY=0
EXIT_ERROR=1
EXIT_WARNING=2
EXIT_CRITICAL=3
EXIT_DOWN=4

# Current exit code
CURRENT_EXIT_CODE=$EXIT_HEALTHY

# Logging functions
log() {
    if [[ "$QUIET" != true ]]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $*" | tee -a "$LOG_FILE"
    fi
}

log_error() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $*" | tee -a "$LOG_FILE" >&2
}

log_warning() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [WARNING] $*" | tee -a "$LOG_FILE"
}

# Print colored output
print_success() {
    if [[ "$QUIET" != true ]]; then
        echo -e "${GREEN}✓ $*${NC}"
    fi
}

print_error() {
    echo -e "${RED}✗ $*${NC}" >&2
    update_exit_code $EXIT_CRITICAL
}

print_warning() {
    echo -e "${YELLOW}⚠ $*${NC}"
    update_exit_code $EXIT_WARNING
}

print_info() {
    if [[ "$QUIET" != true ]]; then
        echo -e "${BLUE}ℹ $*${NC}"
    fi
}

print_debug() {
    if [[ "$VERBOSE" == true ]]; then
        echo -e "${PURPLE}🔍 $*${NC}"
    fi
}

# Update exit code (keep the worst status)
update_exit_code() {
    local new_code=$1
    if [[ $new_code -gt $CURRENT_EXIT_CODE ]]; then
        CURRENT_EXIT_CODE=$new_code
    fi
}

# Help function
show_help() {
    cat << EOF
System Health Monitoring Script for Sistema de Tintas

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -c, --component COMP Component to check: database, redis, api, celery, disk, memory, cpu, all
    -s, --summary        Show health summary for last 24 hours  
    -a, --alerts         Show active alerts
    -r, --report HOURS   Generate health report for specified hours (default: 24)
    -f, --format FORMAT  Output format: text, json, nagios (default: text)
    -q, --quiet          Quiet mode - only errors and warnings
    -v, --verbose        Verbose mode - detailed output
    -h, --help           Show this help message

EXIT CODES:
    0 - All systems healthy
    1 - Script error or invalid arguments  
    2 - Warning conditions detected
    3 - Critical conditions detected
    4 - System down or unavailable

EXAMPLES:
    $0                           # Check all components
    $0 -c database               # Check only database  
    $0 -s                        # Show summary
    $0 -a                        # Show active alerts
    $0 -f json                   # JSON output format
    $0 -r 48 -f nagios           # 48-hour report in Nagios format
    $0 -q -c all                 # Quiet check of all components

MONITORING INTEGRATION:
    # Nagios/Icinga check command
    check_command    check_tintas_health!/path/to/health_check.sh -f nagios -q

    # Cron monitoring (runs every 5 minutes)
    */5 * * * * /path/to/health_check.sh -q -c all || echo "Health check failed" | mail admin@domain.com

    # Zabbix user parameter
    UserParameter=tintas.health[*],/path/to/health_check.sh -c \$1 -f json -q

ENVIRONMENT VARIABLES:
    PYTHON_CMD      Python command (default: python)
    LOG_FILE        Log file path (default: /var/log/tintas-health.log)

EOF
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -c|--component)
                COMPONENT="$2"
                shift 2
                ;;
            -s|--summary)
                SUMMARY=true
                shift
                ;;
            -a|--alerts)
                ALERTS=true
                shift
                ;;
            -r|--report)
                REPORT_HOURS="$2"
                shift 2
                ;;
            -f|--format)
                FORMAT="$2"
                shift 2
                ;;
            -q|--quiet)
                QUIET=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -h|--help)
                HELP=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit $EXIT_ERROR
                ;;
        esac
    done
}

# Check prerequisites
check_prerequisites() {
    print_debug "Checking prerequisites..."

    # Check if manage.py exists
    if [[ ! -f "$MANAGE_PY" ]]; then
        print_error "manage.py not found at $MANAGE_PY"
        exit $EXIT_ERROR
    fi

    # Check Python command
    if ! command -v "$PYTHON_CMD" &> /dev/null; then
        print_error "Python command '$PYTHON_CMD' not found"
        exit $EXIT_ERROR
    fi

    print_debug "Prerequisites check passed"
}

# Validate format
validate_format() {
    case "$FORMAT" in
        text|json|nagios)
            ;;
        *)
            print_error "Invalid format: $FORMAT"
            print_error "Valid formats: text, json, nagios"
            exit $EXIT_ERROR
            ;;
    esac
}

# Validate component
validate_component() {
    if [[ -n "$COMPONENT" ]]; then
        case "$COMPONENT" in
            database|redis|api|celery|disk|memory|cpu|all)
                ;;
            *)
                print_error "Invalid component: $COMPONENT"
                print_error "Valid components: database, redis, api, celery, disk, memory, cpu, all"
                exit $EXIT_ERROR
                ;;
        esac
    fi
}

# Parse Django health check output and update exit code
parse_health_output() {
    local output="$1"
    local exit_code=0

    # Look for health status indicators in output
    if echo "$output" | grep -qi "down\|failed\|error"; then
        if echo "$output" | grep -qi "critical\|down"; then
            exit_code=$EXIT_DOWN
        else
            exit_code=$EXIT_CRITICAL
        fi
    elif echo "$output" | grep -qi "warning\|degraded"; then
        exit_code=$EXIT_WARNING
    elif echo "$output" | grep -qi "healthy\|ok\|good"; then
        exit_code=$EXIT_HEALTHY
    fi

    update_exit_code $exit_code
}

# Run health check command
run_health_check() {
    local cmd_args=()

    if [[ -n "$COMPONENT" ]]; then
        if [[ "$COMPONENT" == "all" ]]; then
            cmd_args+=("--all")
        else
            cmd_args+=("--component" "$COMPONENT")
        fi
    else
        cmd_args+=("--all")
    fi

    print_debug "Running health check with Django management command..."

    local output
    if output=$(cd "$PROJECT_DIR" && $PYTHON_CMD "$MANAGE_PY" health_check "${cmd_args[@]}" 2>&1); then
        echo "$output"
        parse_health_output "$output"
    else
        local cmd_exit_code=$?
        print_error "Health check command failed"
        echo "$output" >&2
        update_exit_code $EXIT_CRITICAL
        return $cmd_exit_code
    fi
}

# Show summary
show_summary() {
    local cmd_args=("--summary")
    
    if [[ -n "$REPORT_HOURS" ]]; then
        cmd_args+=("--hours" "$REPORT_HOURS")
    fi

    print_debug "Generating health summary..."

    local output
    if output=$(cd "$PROJECT_DIR" && $PYTHON_CMD "$MANAGE_PY" health_check "${cmd_args[@]}" 2>&1); then
        echo "$output"
        parse_health_output "$output"
    else
        print_error "Failed to generate health summary"
        echo "$output" >&2
        update_exit_code $EXIT_CRITICAL
        return 1
    fi
}

# Show alerts
show_alerts() {
    print_debug "Retrieving active alerts..."

    local output
    if output=$(cd "$PROJECT_DIR" && $PYTHON_CMD "$MANAGE_PY" health_check --alerts 2>&1); then
        echo "$output"
        
        # Count active alerts to determine exit code
        local alert_count
        alert_count=$(echo "$output" | grep -c "ALERTA\|CRITICAL\|ERROR" || true)
        
        if [[ $alert_count -gt 0 ]]; then
            if echo "$output" | grep -qi "critical"; then
                update_exit_code $EXIT_CRITICAL
            else
                update_exit_code $EXIT_WARNING
            fi
        fi
    else
        print_error "Failed to retrieve alerts"
        echo "$output" >&2
        update_exit_code $EXIT_CRITICAL
        return 1
    fi
}

# Format output for Nagios
format_nagios_output() {
    local status_text
    local performance_data=""

    case $CURRENT_EXIT_CODE in
        $EXIT_HEALTHY)
            status_text="OK - All systems healthy"
            ;;
        $EXIT_WARNING)
            status_text="WARNING - Some systems showing warnings"
            ;;
        $EXIT_CRITICAL)
            status_text="CRITICAL - Critical issues detected"
            ;;
        $EXIT_DOWN)
            status_text="CRITICAL - Systems down or unavailable"
            ;;
        *)
            status_text="UNKNOWN - Unable to determine system status"
            ;;
    esac

    # Add performance data if available (could be enhanced to parse actual metrics)
    echo "$status_text|$performance_data"
}

# Run basic system checks without Django
run_basic_checks() {
    print_info "Running basic system checks..."

    # Check if Python process is running
    if pgrep -f "manage.py" > /dev/null; then
        print_success "Django application is running"
    else
        print_warning "Django application process not found"
    fi

    # Check disk space
    local disk_usage
    disk_usage=$(df "$PROJECT_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [[ $disk_usage -lt 80 ]]; then
        print_success "Disk usage is healthy ($disk_usage%)"
    elif [[ $disk_usage -lt 90 ]]; then
        print_warning "Disk usage is high ($disk_usage%)"
    else
        print_error "Disk usage is critical ($disk_usage%)"
    fi

    # Check load average
    local load_avg
    load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    local cpu_count
    cpu_count=$(nproc)
    local load_threshold
    load_threshold=$((cpu_count * 2))

    if (( $(echo "$load_avg < $load_threshold" | bc -l 2>/dev/null || echo "0") )); then
        print_success "System load is healthy ($load_avg)"
    else
        print_warning "System load is high ($load_avg)"
    fi
}

# Main function
main() {
    # Parse command line arguments
    parse_arguments "$@"

    # Show help if requested
    if [[ "$HELP" == true ]]; then  
        show_help
        exit $EXIT_HEALTHY
    fi

    # Validate arguments
    validate_format
    validate_component

    if [[ "$VERBOSE" == true ]]; then
        print_info "Starting system health monitoring..."
        log "Health check script started with arguments: $*"
    fi

    # Check prerequisites
    check_prerequisites

    # Run basic checks first
    if [[ "$COMPONENT" == "" || "$COMPONENT" == "all" ]]; then
        run_basic_checks
    fi

    # Execute requested operation
    if [[ "$SUMMARY" == true ]]; then
        show_summary
    elif [[ "$ALERTS" == true ]]; then
        show_alerts
    else
        # Try to run Django health check, fallback to basic checks if it fails
        if ! run_health_check; then
            print_warning "Django health check failed, running basic checks only"
            run_basic_checks
        fi
    fi

    # Format output based on requested format
    case "$FORMAT" in
        nagios)
            format_nagios_output
            ;;
        json)
            # JSON output would require more complex parsing
            echo "{\"status\": \"$CURRENT_EXIT_CODE\", \"timestamp\": \"$(date -Is)\"}"
            ;;
        text)
            # Default text output (already displayed above)
            ;;
    esac

    if [[ "$VERBOSE" == true ]]; then
        case $CURRENT_EXIT_CODE in
            $EXIT_HEALTHY)
                print_success "Health check completed - all systems healthy"
                ;;
            $EXIT_WARNING)
                print_warning "Health check completed - warnings detected"
                ;;
            $EXIT_CRITICAL)
                print_error "Health check completed - critical issues found"
                ;;
            $EXIT_DOWN)
                print_error "Health check completed - systems down"
                ;;
        esac
        
        log "Health check script completed with exit code: $CURRENT_EXIT_CODE"
    fi

    exit $CURRENT_EXIT_CODE
}

# Parse arguments and run main function
main "$@"
#!/usr/bin/env python3
"""
Gunicorn Configuration for Atalaia Tintas Paint Store System
Production WSGI server configuration with blue-green deployment support

This configuration provides:
- Multi-worker process management
- Performance optimization for paint store operations
- Health checks and monitoring
- Blue-green deployment compatibility
- Security and logging settings
"""

import multiprocessing
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

# Import environment-specific settings
try:
    from tintas_system.settings.production import *
except ImportError:
    from tintas_system.settings.base import *

# ================================
# Server Configuration
# ================================

# WSGI application
wsgi_app = "tintas_system.wsgi:application"

# Deployment environment (blue/green)
deployment_env = os.environ.get('DEPLOYMENT_ENV', 'blue')

# ================================
# Network Configuration
# ================================

# Bind addresses for blue-green deployment
if deployment_env == 'green':
    bind = [
        "127.0.0.1:8002",  # Primary green
        "127.0.0.1:8003",  # Secondary green
    ]
else:  # Default to blue
    bind = [
        "127.0.0.1:8000",  # Primary blue  
        "127.0.0.1:8001",  # Secondary blue
    ]

# Backlog - Maximum number of pending connections
backlog = 2048

# ================================
# Worker Configuration
# ================================

# Number of worker processes
# For paint store: CPU intensive operations (color matching, calculations)
# Formula: (2 x CPU cores) + 1, with minimum 3 for high availability
cpu_count = multiprocessing.cpu_count()
workers = max(3, (2 * cpu_count) + 1)

# Worker class - sync for Django compatibility
worker_class = "sync"

# Worker connections - for sync workers, this is typically 1
worker_connections = 1000

# Maximum requests per worker before restart (prevents memory leaks)
max_requests = 1000
max_requests_jitter = 50

# Worker timeout settings
timeout = 120  # Increased for complex paint calculations
keepalive = 5  # Keep-alive connections

# Graceful timeout for deployments
graceful_timeout = 60

# ================================
# Process Management
# ================================

# Preload application for faster worker startup
preload_app = True

# Restart workers automatically
max_worker_memory = 300  # MB - restart worker if memory exceeds this
worker_tmp_dir = "/dev/shm"  # Use memory for temp files (Linux)

# Process naming for monitoring
proc_name = f"tintas_system_{deployment_env}"

# ================================
# Logging Configuration  
# ================================

# Log level
loglevel = "info"

# Log file paths
log_dir = PROJECT_ROOT / "logs"
log_dir.mkdir(exist_ok=True)

# Access log
accesslog = str(log_dir / f"gunicorn_access_{deployment_env}.log")

# Error log  
errorlog = str(log_dir / f"gunicorn_error_{deployment_env}.log")

# Access log format (includes deployment info)
access_log_format = (
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s '
    '"%(f)s" "%(a)s" %(D)s %(p)s [' + deployment_env + ']'
)

# Disable access log to stdout (use file only)
disable_redirect_access_to_syslog = True

# Capture stdout/stderr to error log
capture_output = True

# ================================
# Security Configuration
# ================================

# Limit request line size (prevent DoS)
limit_request_line = 4096

# Limit request header field size
limit_request_field_size = 8190  

# Limit number of request header fields
limit_request_fields = 100

# ================================
# Performance Configuration
# ================================

# Enable sendfile for static files (if served by Gunicorn)
sendfile = True

# Buffer size for reading requests
# Optimized for paint store data (product info, color formulas)
forwarded_allow_ips = "127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"

# ================================
# Health Check Configuration
# ================================

def when_ready(server):
    """Called when the server is started."""
    server.log.info(f"Atalaia Tintas {deployment_env} environment ready")
    server.log.info(f"Workers: {workers}, Bind: {bind}")

def worker_int(worker):
    """Called when a worker receives the INT or QUIT signal."""
    worker.log.info(f"Worker {worker.pid} received interrupt signal")

def pre_fork(server, worker):
    """Called before a worker is forked."""
    server.log.info(f"Worker {worker.age} about to be forked")

def post_fork(server, worker):
    """Called after a worker is forked."""
    server.log.info(f"Worker {worker.pid} forked successfully")

def pre_exec(server):
    """Called before a new master process is forked."""
    server.log.info("Forked child, re-executing")

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.error(f"Worker {worker.pid} aborted!")
    
    # Log worker state for debugging
    import traceback
    import sys
    
    worker.log.error("Worker traceback:")
    worker.log.error(traceback.format_exc())

# ================================
# Application-Specific Configuration  
# ================================

# Environment variables for Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tintas_system.settings.production')
os.environ.setdefault('DEPLOYMENT_ENV', deployment_env)

# Paint Store Specific Settings
tmp_upload_dir = None  # Let Django handle temporary files

# Enable thread safety for paint color calculations
enable_stdio_inheritance = True

# ================================
# Development Overrides
# ================================

# Override settings for development/testing
if os.environ.get('DEBUG') == 'True':
    # Development settings
    loglevel = "debug"
    reload = True
    reload_extra_files = [
        BASE_DIR / "tintas_system" / "settings",
        BASE_DIR / "apps",
        BASE_DIR / "templates",
    ]
    
    # Reduce workers for development
    workers = 2

# ================================
# Monitoring Hooks
# ================================

def post_worker_init(worker):
    """Called after a worker has initialized the application."""
    import logging
    
    # Set up application monitoring
    logger = logging.getLogger('gunicorn.error')
    
    # Initialize paint store monitoring
    try:
        from apps.monitoring.services import SystemHealthService
        health_service = SystemHealthService()
        logger.info(f"Worker {worker.pid}: Monitoring initialized")
    except ImportError:
        logger.warning(f"Worker {worker.pid}: Monitoring service not available")

def worker_exit(server, worker):
    """Called when a worker is exiting."""
    server.log.info(f"Worker {worker.pid} exiting")

# ================================
# Blue-Green Deployment Helpers
# ================================

def on_starting(server):
    """Called during server startup."""
    # Create deployment marker file for health checks
    marker_path = PROJECT_ROOT / f".deployment_{deployment_env}"
    marker_path.touch()
    
    server.log.info(f"Created deployment marker: {marker_path}")

def on_exit(server):
    """Called during server shutdown."""
    # Clean up deployment marker
    marker_path = PROJECT_ROOT / f".deployment_{deployment_env}"
    if marker_path.exists():
        marker_path.unlink()
        server.log.info(f"Removed deployment marker: {marker_path}")

# ================================
# SSL Configuration (if terminating SSL at Gunicorn level)
# ================================

# Uncomment if SSL termination is at Gunicorn level instead of Nginx
# keyfile = "/path/to/ssl/private/key.pem"
# certfile = "/path/to/ssl/certificate/cert.pem"
# ssl_version = ssl.PROTOCOL_TLS
# ciphers = "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS"

# ================================
# Paint Store Business Logic Optimization
# ================================

# Custom configuration for paint store operations
def paint_store_worker_setup():
    """Initialize worker for paint store specific operations."""
    
    # Pre-load color calculation libraries
    try:
        import numpy as np
        import pandas as pd
        # Pre-load common color space calculations
        np.seterr(all='raise')  # Strict error handling for color calculations
    except ImportError:
        pass
    
    # Initialize database connections pool for high-frequency operations
    from django.db import connections
    db_alias = connections['default']
    
    # Warm up Django cache
    from django.core.cache import cache
    cache.get('_health_check_')

# Hook the paint store setup
post_worker_init = paint_store_worker_setup
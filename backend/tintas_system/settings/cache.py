# -*- coding: utf-8 -*-
"""
Cache Configuration for Permission System
Optimized Redis configuration for permission data storage with
high performance, reliability, and monitoring capabilities.
"""

import os
from typing import Dict, Any

# Redis Cache Configuration for Permission System

# Redis connection settings
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 1))  # Use DB 1 for permissions
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

# Connection pool settings for optimal performance
REDIS_CONNECTION_POOL_KWARGS = {
    'max_connections': 50,
    'retry_on_timeout': True,
    'socket_keepalive': True,
    'socket_keepalive_options': {},
    'health_check_interval': 30,  # seconds
}

# Build Redis connection URL
if REDIS_PASSWORD:
    REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
else:
    REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# Django Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': REDIS_CONNECTION_POOL_KWARGS,
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            
            # Permission-optimized settings
            'IGNORE_EXCEPTIONS': True,  # Graceful failover to database
            'LOG_IGNORED_EXCEPTIONS': True,
            
            # Redis client options for performance
            'REDIS_CLIENT_KWARGS': {
                'decode_responses': True,
                'socket_timeout': 5,  # 5 second socket timeout
                'socket_connect_timeout': 5,
                'retry_on_timeout': True,
                'encoding': 'utf-8',
            },
            
            # Key prefix for permission system
            'KEY_PREFIX': 'tintas_permissions',
            'VERSION': 1,
        },
        'TIMEOUT': 3600,  # Default timeout: 1 hour
        'KEY_FUNCTION': 'core.cache.make_permission_cache_key',
    },
    
    # Dedicated cache for session data (if needed)
    'sessions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"redis://{REDIS_HOST}:{REDIS_PORT}/2",  # Use DB 2 for sessions
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': REDIS_CONNECTION_POOL_KWARGS,
            'KEY_PREFIX': 'tintas_sessions',
        },
        'TIMEOUT': 86400,  # 24 hours for sessions
    },
    
    # Dedicated cache for temporary data
    'temporary': {
        'BACKEND': 'django_redis.cache.RedisCache', 
        'LOCATION': f"redis://{REDIS_HOST}:{REDIS_PORT}/3",  # Use DB 3 for temporary data
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': REDIS_CONNECTION_POOL_KWARGS,
            'KEY_PREFIX': 'tintas_temp',
        },
        'TIMEOUT': 300,  # 5 minutes for temporary data
    }
}

# Cache Key Configuration for Permission System
PERMISSION_CACHE_SETTINGS = {
    # Cache timeout configurations (seconds)
    'TIMEOUTS': {
        'user_permissions': 3600,      # 1 hour - individual user permissions
        'group_permissions': 7200,     # 2 hours - group permissions (change less frequently)
        'user_groups': 1800,          # 30 minutes - user group memberships
        'permission_hierarchy': 14400, # 4 hours - permission hierarchy data
        'effective_permissions': 1800, # 30 minutes - computed effective permissions
        'permission_metadata': 86400,  # 24 hours - permission metadata
        'audit_metadata': 43200,      # 12 hours - audit log metadata
    },
    
    # Cache key prefixes with namespacing
    'KEY_PREFIXES': {
        'user_permissions': 'perm:user:{}',
        'group_permissions': 'perm:group:{}',
        'user_groups': 'groups:user:{}',
        'permission_hierarchy': 'perm:hierarchy:{}',
        'effective_permissions': 'perm:effective:{}',
        'permission_metadata': 'perm:meta:{}',
        'audit_metadata': 'audit:meta:{}',
    },
    
    # Performance optimization settings
    'BATCH_SIZE': 50,              # Batch size for cache operations
    'WARMING_DELAY': 0.1,          # Delay between warming batches (seconds)
    'MAX_KEY_LENGTH': 250,         # Maximum cache key length
    'COMPRESSION_THRESHOLD': 1024, # Compress values larger than 1KB
    
    # Monitoring and alerting thresholds
    'PERFORMANCE_THRESHOLDS': {
        'min_hit_ratio': 0.90,        # 90% minimum hit ratio
        'max_avg_response_time': 50.0, # 50ms maximum average response time
        'max_error_rate': 0.01,       # 1% maximum error rate
        'max_memory_usage': '500MB',  # Maximum Redis memory usage
    },
    
    # Cache invalidation settings
    'INVALIDATION': {
        'batch_invalidation': True,    # Use batch invalidation for efficiency
        'cascade_invalidation': True,  # Cascade invalidation to dependent keys
        'async_invalidation': False,   # Use synchronous invalidation for consistency
    },
    
    # Failover and reliability settings
    'FAILOVER': {
        'enable_graceful_degradation': True,  # Fall back to database on Redis failure
        'health_check_interval': 30,          # Health check every 30 seconds
        'retry_attempts': 3,                  # Retry failed operations 3 times
        'retry_delay': 1.0,                   # 1 second delay between retries
    }
}

# Redis Configuration Optimization
REDIS_OPTIMIZATION_SETTINGS = {
    # Memory optimization
    'maxmemory_policy': 'allkeys-lru',  # Evict least recently used keys
    'maxmemory': os.getenv('REDIS_MAX_MEMORY', '256mb'),
    
    # Persistence settings
    'save': '900 1 300 10 60 10000',  # Save snapshots based on key changes
    'appendonly': 'yes',               # Enable append-only file for durability
    'appendfsync': 'everysec',        # Sync append-only file every second
    
    # Performance tuning
    'tcp_keepalive': '300',           # TCP keepalive timeout
    'timeout': '0',                   # Client idle timeout (0 = no timeout)
    'tcp_backlog': '511',            # TCP listen backlog
    
    # Security settings
    'protected_mode': 'yes',         # Enable protected mode
    'bind': '127.0.0.1',            # Bind to localhost only (adjust for production)
    
    # Logging and monitoring
    'loglevel': 'notice',            # Log level: debug, verbose, notice, warning
    'syslog_enabled': 'yes',         # Enable syslog
    'syslog_ident': 'tintas-redis', # Syslog identifier
}

# Cache Warming Configuration
CACHE_WARMING_SETTINGS = {
    'ENABLED': True,                 # Enable automatic cache warming
    'STARTUP_WARMING': True,         # Warm cache on application startup
    'SCHEDULED_WARMING': True,       # Enable scheduled cache warming
    'WARMING_SCHEDULE': '0 */4 * * *',  # Warm cache every 4 hours (cron format)
    
    'WARMING_STRATEGIES': {
        'active_users': {
            'enabled': True,
            'lookback_days': 30,     # Consider users active in last 30 days
            'max_users': 100,       # Warm cache for top 100 active users
        },
        'all_groups': {
            'enabled': True,
            'max_groups': 50,       # Warm cache for up to 50 groups
        },
        'permission_metadata': {
            'enabled': True,
            'include_inactive': False,  # Only warm active permissions
        },
    },
    
    'WARMING_LIMITS': {
        'max_duration': 300,        # Maximum warming duration (5 minutes)
        'batch_size': 10,          # Process 10 items per batch
        'batch_delay': 0.1,        # 100ms delay between batches
        'memory_threshold': 0.8,   # Stop warming if Redis memory > 80%
    }
}

# Cache Monitoring Configuration  
CACHE_MONITORING_SETTINGS = {
    'ENABLED': True,                # Enable cache performance monitoring
    'METRICS_RETENTION': 86400,     # Keep metrics for 24 hours
    'ALERT_THRESHOLDS': PERMISSION_CACHE_SETTINGS['PERFORMANCE_THRESHOLDS'],
    
    'LOGGING': {
        'log_cache_hits': False,    # Don't log individual cache hits (too verbose)  
        'log_cache_misses': True,   # Log cache misses for analysis
        'log_invalidations': True,  # Log cache invalidations
        'log_performance_alerts': True,  # Log performance threshold violations
    },
    
    'METRICS_COLLECTION': {
        'collect_hit_ratio': True,
        'collect_response_times': True,
        'collect_error_rates': True,
        'collect_memory_usage': True,
        'collect_key_counts': True,
    },
    
    'HEALTH_CHECKS': {
        'redis_connectivity': True,  # Check Redis connectivity
        'memory_usage': True,       # Check Redis memory usage
        'response_times': True,     # Check response time thresholds
        'error_rates': True,        # Check error rate thresholds
    }
}

# Environment-specific cache configurations

# Development environment settings
if os.getenv('DJANGO_ENV') == 'development':
    # Use less aggressive caching in development
    PERMISSION_CACHE_SETTINGS['TIMEOUTS'] = {
        key: min(value, 300) for key, value in  # Max 5 minutes in dev
        PERMISSION_CACHE_SETTINGS['TIMEOUTS'].items()
    }
    
    # Enable more verbose logging
    CACHE_MONITORING_SETTINGS['LOGGING']['log_cache_hits'] = True
    
    # Shorter warming intervals for testing
    CACHE_WARMING_SETTINGS['WARMING_SCHEDULE'] = '*/30 * * * *'  # Every 30 minutes

# Production environment settings  
elif os.getenv('DJANGO_ENV') == 'production':
    # Use Redis Sentinel for high availability in production
    REDIS_SENTINELS = os.getenv('REDIS_SENTINELS', '').split(',')
    if REDIS_SENTINELS and REDIS_SENTINELS[0]:
        CACHES['default']['LOCATION'] = [
            f"{host.strip()}:26379" for host in REDIS_SENTINELS
        ]
        CACHES['default']['OPTIONS']['SENTINEL_SERVICE_NAME'] = 'mymaster'
    
    # Production performance optimizations
    REDIS_CONNECTION_POOL_KWARGS['max_connections'] = 100
    CACHE_WARMING_SETTINGS['WARMING_LIMITS']['max_duration'] = 600  # 10 minutes
    
    # Enhanced monitoring in production
    CACHE_MONITORING_SETTINGS['METRICS_RETENTION'] = 604800  # 7 days

# Test environment settings
elif os.getenv('DJANGO_ENV') == 'test':
    # Use dummy cache for testing to avoid Redis dependency
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }
    
    # Disable cache warming in tests
    CACHE_WARMING_SETTINGS['ENABLED'] = False
    CACHE_MONITORING_SETTINGS['ENABLED'] = False

# Utility functions for cache configuration

def get_cache_config() -> Dict[str, Any]:
    """Get the complete cache configuration"""
    return {
        'caches': CACHES,
        'permission_settings': PERMISSION_CACHE_SETTINGS,
        'warming_settings': CACHE_WARMING_SETTINGS,
        'monitoring_settings': CACHE_MONITORING_SETTINGS,
        'redis_optimization': REDIS_OPTIMIZATION_SETTINGS,
    }

def make_permission_cache_key(key: str, key_prefix: str, version: int) -> str:
    """
    Custom cache key function for permission system
    
    Args:
        key: Base cache key
        key_prefix: Cache key prefix from settings
        version: Cache version
        
    Returns:
        Formatted cache key string
    """
    # Ensure key length doesn't exceed Redis limits
    max_length = PERMISSION_CACHE_SETTINGS['MAX_KEY_LENGTH']
    
    formatted_key = f"{key_prefix}:v{version}:{key}"
    
    if len(formatted_key) > max_length:
        # Hash the key if it's too long
        import hashlib
        key_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
        formatted_key = f"{key_prefix}:v{version}:hash:{key_hash}"
    
    return formatted_key

def validate_cache_configuration() -> Dict[str, Any]:
    """
    Validate cache configuration and return status
    
    Returns:
        Dictionary with validation results
    """
    validation_results = {
        'valid': True,
        'errors': [],
        'warnings': [],
    }
    
    try:
        # Check Redis connection
        from django.core.cache import cache
        cache.set('_validation_test', 'test_value', timeout=10)
        test_value = cache.get('_validation_test')
        
        if test_value != 'test_value':
            validation_results['errors'].append("Redis cache validation failed")
            validation_results['valid'] = False
        else:
            cache.delete('_validation_test')
            
    except Exception as e:
        validation_results['errors'].append(f"Redis connection failed: {str(e)}")
        validation_results['valid'] = False
    
    # Validate configuration values
    timeout_values = PERMISSION_CACHE_SETTINGS['TIMEOUTS']
    if any(timeout <= 0 for timeout in timeout_values.values()):
        validation_results['errors'].append("Invalid timeout values detected")
        validation_results['valid'] = False
    
    # Check memory settings
    max_memory = REDIS_OPTIMIZATION_SETTINGS.get('maxmemory', '256mb')
    if not max_memory.endswith(('mb', 'gb', 'MB', 'GB')):
        validation_results['warnings'].append("Redis maxmemory setting should specify units (mb/gb)")
    
    # Validate performance thresholds
    thresholds = PERMISSION_CACHE_SETTINGS['PERFORMANCE_THRESHOLDS']
    if thresholds['min_hit_ratio'] <= 0 or thresholds['min_hit_ratio'] > 1:
        validation_results['errors'].append("Invalid hit ratio threshold")
        validation_results['valid'] = False
    
    return validation_results

# Export configuration for Django settings
__all__ = [
    'CACHES',
    'PERMISSION_CACHE_SETTINGS', 
    'CACHE_WARMING_SETTINGS',
    'CACHE_MONITORING_SETTINGS',
    'REDIS_OPTIMIZATION_SETTINGS',
    'get_cache_config',
    'make_permission_cache_key',
    'validate_cache_configuration',
]
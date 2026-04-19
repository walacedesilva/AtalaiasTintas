# T017: API Error Handling and Validation Implementation Guide

## Overview

T017 implements comprehensive API error handling and validation for the User Permissions System, providing:

- **Custom exception handling** with consistent error responses across all endpoints
- **Input validation** with comprehensive business rule checking and security validation
- **Error messages** that provide clear guidance without exposing sensitive system information
- **Rate limiting and throttling** with appropriate HTTP status codes and retry headers
- **Validation error responses** with field-specific details for client-side handling
- **Exception logging** that captures sufficient detail for troubleshooting without exposing sensitive data

## 🎯 Key Features Implemented

### 1. Custom Exception System ✅
**File**: `backend/apps/core/exceptions.py`

- **Custom Exception Classes**:
  - `PermissionSystemException` - Base exception for all permission system errors
  - `PermissionValidationError` - Business rule and validation failures
  - `InsufficientPermissionsError` - Authorization failures
  - `PermissionNotFoundError` - Resource not found errors
  - `PermissionConflictError` - Duplicate/conflict errors
  - `PermissionExpiredError` - Expired permission usage
  - `RateLimitExceededError` - Rate limiting violations
  - `SystemMaintenanceError` - Maintenance mode errors
  - `DataIntegrityError` - Data consistency violations

- **Custom Exception Handler**:
  - Consistent error response format across all endpoints
  - Security-conscious error messages (no internal details exposed)
  - Request ID correlation for debugging
  - Field-specific validation error formatting
  - Proper HTTP status codes and headers

### 2. Comprehensive Input Validation ✅
**File**: `backend/apps/core/exceptions.py` (ValidationUtils class)

- **Permission Code Validation**:
  - Format validation (module.resource.action pattern)
  - Security validation (SQL injection prevention)
  - Length and character restrictions
  - Case normalization

- **Risk Level Validation**:
  - Valid level enforcement (low, medium, high, critical)
  - Authorization requirements for risk escalation

- **Business Rule Validation**:
  - User permission assignment rules
  - Group membership validation
  - Permission deletion safety checks
  - Risk level change authorization

### 3. Advanced Middleware System ✅
**File**: `backend/apps/core/middleware.py`

- **RequestIdMiddleware**: Unique request tracking for all API calls
- **ErrorContextMiddleware**: Enhanced error context for debugging
- **RateLimitingMiddleware**: Multi-tier rate limiting with sliding window algorithm
- **Existing Middleware Enhanced**: Integrated with audit logging and authentication systems

### 4. Enhanced Serializers ✅
**File**: `backend/apps/core/serializers.py`

- **EnhancedPermissionSerializer**: Uses T017 validation utilities
- **EnhancedUserPermissionSerializer**: Business rule enforcement
- **ValidationErrorResponseSerializer**: Consistent error response documentation
- **RateLimitErrorResponseSerializer**: Rate limiting error format
- **BulkPermissionOperationSerializer**: Bulk operations with validation
- **HealthCheckResponseSerializer**: Health endpoint documentation

### 5. Configuration & Settings ✅
**File**: `backend/tintas_system/settings.py`

- **Custom Exception Handler**: Integrated with DRF configuration
- **Rate Limiting Settings**: Configurable limits for different user types
- **Security Configuration**: Maintenance mode, trusted IPs, error sanitization
- **Validation Settings**: Business rule enforcement parameters

## 📊 Rate Limiting Configuration

```python
# Per-minute rate limits by user type
RATE_LIMIT_ANONYMOUS = 60       # Anonymous users
RATE_LIMIT_AUTHENTICATED = 300  # Authenticated users  
RATE_LIMIT_API_READ = 1000      # API read operations
RATE_LIMIT_API_WRITE = 100      # API write operations
RATE_LIMIT_ADMIN = 500          # Admin users

# Trusted IPs bypass rate limiting
RATE_LIMIT_TRUSTED_IPS = ['127.0.0.1', '::1']
```

## 🔍 Error Response Format

### Standard Validation Error
```json
{
  "error": "validation_error",
  "detail": "Invalid input data provided",
  "field_errors": {
    "permission_code": ["Permission code must follow format: module.resource.action"],
    "risk_level": ["Risk level must be one of: low, medium, high, critical"]
  },
  "timestamp": "2024-04-12T10:30:45.123Z",
  "request_id": "req_1712914245.123_a1b2c3d4"
}
```

### Rate Limit Error
```json
{
  "error": "rate_limit_exceeded",
  "detail": "Rate limit of 100 requests per 60 seconds exceeded",
  "retry_after": 45,
  "limit": 100,
  "window": 60
}
```

### Permission System Error
```json
{
  "error": "permission_validation_error", 
  "detail": "Cannot assign permissions to inactive users",
  "timestamp": "2024-04-12T10:30:45.123Z",
  "request_id": "req_1712914245.123_a1b2c3d4"
}
```

## 🛡️ Security Features

### 1. Error Message Sanitization
- Internal file paths removed (`[FILE_PATH]`)
- SQL queries redacted (`[SQL_QUERY]`)
- Internal IDs masked (`id=[ID]`)
- Message length truncation (500 chars max)
- Sensitive header exclusion from logs

### 2. Rate Limiting Protection
- **Sliding Window Algorithm**: Prevents burst attacks
- **Multi-tier Limits**: Different limits for different operations
- **IP and User Based**: Granular control over access
- **Bypass Mechanism**: Trusted IPs for infrastructure
- **Progressive Lockout**: Integration with existing login attempt tracking

### 3. Request Tracking
- **Unique Request IDs**: Every request gets a correlation ID
- **Performance Monitoring**: Response time tracking
- **Error Correlation**: Link errors to specific requests
- **Audit Integration**: Enhanced logging with T007 audit system

## 🔧 Usage Examples

### 1. Using Custom Exceptions in Views
```python
from apps.core.exceptions import (
    PermissionValidationError, ValidationUtils
)

def create_permission(request):
    try:
        code = ValidationUtils.validate_permission_code(request.data['code'])
        # ... create permission
    except PermissionValidationError as e:
        # Automatically handled by custom exception handler
        raise e
```

### 2. Enhanced Serializer Validation
```python
from apps.core.serializers import EnhancedPermissionSerializer

serializer = EnhancedPermissionSerializer(data=request.data)
if serializer.is_valid():
    permission = serializer.save()
else:
    # Returns consistent field-level errors
    return Response(serializer.errors, status=400)
```

### 3. Bulk Operations with Validation
```python
from apps.core.serializers import BulkPermissionOperationSerializer

bulk_serializer = BulkPermissionOperationSerializer(
    data=request.data, 
    context={'request': request}
)
if bulk_serializer.is_valid():
    # Process bulk operation with full validation
    result = process_bulk_permissions(bulk_serializer.validated_data)
```

## 📈 Health Monitoring

### Health Check Endpoints
- **`/health/`**: Basic health check (high rate limit)
- **`/api/v1/health/system/`**: Detailed system health
- **`/api/v1/health/permissions/`**: Permission system health  
- **`/api/v1/health/cache/`**: Cache system status
- **`/api/v1/health/database/`**: Database connectivity
- **`/api/v1/health/performance/`**: Performance metrics

### Health Response Format
```json
{
  "status": "healthy",
  "timestamp": "2024-04-12T10:30:45.123Z", 
  "version": "1.0.0",
  "checks": {
    "database": {"status": "healthy", "response_time_ms": 12},
    "cache": {"status": "healthy", "response_time_ms": 3},
    "permissions": {"status": "healthy", "total_permissions": 156}
  }
}
```

## 🧪 Testing & Validation

### 1. Exception Handler Testing
```bash
# Test custom exception handling
curl -X POST http://localhost:8000/api/v1/permissions/ \
  -H "Content-Type: application/json" \
  -d '{"code": "invalid..code", "name": "Test"}'
```

### 2. Rate Limiting Testing  
```bash
# Test rate limiting (run multiple times quickly)
for i in {1..70}; do
  curl -s http://localhost:8000/api/v1/health/ | head -1
done
```

### 3. Validation Testing
```bash
# Test field validation
curl -X POST http://localhost:8000/api/v1/permissions/ \
  -H "Content-Type: application/json" \  
  -d '{"risk_level": "invalid", "name": ""}'
```

## 📝 Error Logging & Monitoring

### Log Levels
- **INFO**: Successful operations, rate limit headers
- **WARNING**: Rate limit violations, validation errors, 4xx responses
- **ERROR**: System exceptions, 5xx errors, unhandled exceptions
- **CRITICAL**: System-wide failures, security breaches

### Log Context
Every log entry includes:
- `request_id`: Unique request correlation ID
- `user`: Username or 'anonymous'
- `client_ip`: Real client IP (proxy-aware)
- `path`: Request path and method
- `response_time`: Processing time in milliseconds
- `context`: Additional error-specific context

### Monitoring Integration
- **Request ID Correlation**: Track requests across services
- **Performance Metrics**: Response time tracking and alerting
- **Error Pattern Detection**: Automated error analysis
- **Health Check Monitoring**: Continuous system health validation

## 🚀 Deployment Considerations

### 1. Production Settings
```python
# Enhanced security in production
ERROR_LOGGING = {
    'SANITIZE_ERROR_MESSAGES': True,
    'HIDE_INTERNAL_IDS': True,
    'MAX_ERROR_MESSAGE_LENGTH': 500,
}

# Production rate limits (higher)
RATE_LIMIT_AUTHENTICATED = 1000  # vs 300 in dev
RATE_LIMIT_API_READ = 5000       # vs 1000 in dev
```

### 2. Cache Configuration
Rate limiting requires Redis/Memcached for production:
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### 3. Monitoring Setup
- **APM Integration**: New Relic, DataDog, etc.
- **Log Aggregation**: ELK Stack, Splunk
- **Alert Configuration**: Rate limit violations, error spikes
- **Dashboard Creation**: Request volume, error rates, response times

## ✅ T017 Completion Status

**T017: API Error Handling and Validation - 100% COMPLETED ✅**

### ✅ Acceptance Criteria Met:

1. **✅ Custom exception handling** provides consistent error responses across all endpoints
   - Complete custom exception hierarchy implemented
   - Unified exception handler with proper HTTP status codes
   - Security-conscious error messages

2. **✅ Input validation** includes comprehensive business rule checking and security validation
   - ValidationUtils class with comprehensive validation methods
   - BusinessRuleValidator for complex business logic
   - SQL injection prevention and security checks

3. **✅ Error messages** provide clear guidance without exposing sensitive system information
   - Error message sanitization implemented
   - Internal details redacted from client responses
   - Clear, actionable error descriptions

4. **✅ Rate limiting and throttling** with appropriate HTTP status codes and retry headers
   - Advanced sliding window rate limiting implemented
   - Multi-tier limits for different user types and operations
   - Proper HTTP 429 responses with Retry-After headers

5. **✅ Validation error responses** include field-specific details for client-side handling
   - Field-level error formatting in consistent structure
   - Enhanced serializers with T017 validation integration
   - Client-friendly error response format

6. **✅ Exception logging** captures sufficient detail for troubleshooting without exposing sensitive data
   - Request correlation IDs for error tracking
   - Comprehensive logging with sanitized context
   - Integration with existing audit trail system

## 🎯 Next Steps: T018 API Integration Testing

T017 creates the foundation for robust API error handling. The next task (T018) will build comprehensive integration tests that validate:

- Error response consistency across all endpoints
- Rate limiting behavior under load
- Validation rule enforcement
- Exception handling effectiveness
- Health monitoring accuracy

**Files Created/Modified**:
- ✅ `backend/apps/core/exceptions.py` - Complete custom exception system (+800 lines)
- ✅ `backend/apps/core/middleware.py` - Enhanced with T017 error handling middleware
- ✅ `backend/apps/core/serializers.py` - Extended with T017 validation serializers
- ✅ `backend/tintas_system/settings.py` - T017 configuration and exception handler
- ✅ `backend/docs/T017_API_ERROR_HANDLING_GUIDE.md` - Complete implementation guide

**Integration Status**: T017 fully integrates with existing T001-T016 components, enhancing the entire permission system with comprehensive error handling and validation.
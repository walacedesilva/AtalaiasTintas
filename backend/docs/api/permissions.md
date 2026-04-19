# Permission System API Documentation

**Version**: 1.0.0  
**T015**: Complete API documentation with troubleshooting guidance and migration paths

## Overview

The AtalaiasTintas Permission System API provides comprehensive permission management capabilities with enterprise-grade security, performance optimization, and extensive audit features.

### Key Features

- 🔐 **Granular Permission Management**: Fine-grained control over system permissions
- 👥 **Role-Based Access Control**: Group-based permission inheritance
- ⏰ **Temporal Permissions**: Time-limited permission assignments
- 🚀 **Performance Optimized**: T014 optimizations with caching and compression
- 📊 **Analytics & Monitoring**: Risk analysis and usage statistics
- 🛡️ **Security First**: Audit trails and risk-based classification

## Authentication

All API endpoints require authentication using one of the following methods:

### Token Authentication (Recommended)
```http
Authorization: Token your-auth-token-here
```

### Session Authentication
Use Django session cookies for web interface integration.

## Base URL

- **Development**: `http://localhost:8000/api/`
- **Staging**: `https://api-staging.atalaiaspintas.com/api/`
- **Production**: `https://api.atalaiaspintas.com/api/`

## API Endpoints

### Permissions Management

#### List Permissions
```http
GET /permissions/
```

**Query Parameters**:
- `page` (int): Page number for pagination (default: 1)
- `page_size` (int): Items per page (default: 25)
- `module` (string): Filter by module name
- `risk_level` (enum): Filter by risk level (`low`, `medium`, `high`, `critical`)
- `is_active` (boolean): Filter by active status
- `search` (string): Search in name, code, description
- `ordering` (string): Sort field (prefix with `-` for descending)

**Response Structure**:
```json
{
  "count": 150,
  "next": "http://localhost:8000/api/permissions/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "View Users",
      "code": "users.view",
      "description": "Allows viewing user information",
      "module": "users",
      "risk_level": "low",
      "is_active": true,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**Performance Features (T014)**:
- Response caching (5 minutes)
- Gzip compression
- Optimized database queries
- Performance metrics tracking

#### Create Permission
```http
POST /permissions/
```

**Required Permissions**: `PERMISSION_MANAGEMENT_WRITE`

**Request Body**:
```json
{
  "name": "Delete Reports",
  "code": "reports.delete",
  "description": "Allows deletion of system reports",
  "module": "reports",
  "risk_level": "high"
}
```

**Validation Rules**:
- `code` must be unique across the system
- `risk_level` must be one of: `low`, `medium`, `high`, `critical`
- `name` and `module` are required

#### Get Permission Details
```http
GET /permissions/{id}/
```

**Response includes**:
- Complete permission details
- Assignment statistics
- Audit information
- Related permissions

#### Update Permission
```http
PUT /permissions/{id}/
PATCH /permissions/{id}/
```

**Security Considerations**:
- Risk level changes trigger additional validation
- High-risk permissions require confirmation for modifications

#### Delete Permission
```http
DELETE /permissions/{id}/
```

**Query Parameters**:
- `confirm_high_risk_deletion` (boolean): Required for high/critical risk permissions

**Safety Features**:
- Soft delete with audit trail
- High-risk permissions require explicit confirmation
- Validates impact on existing assignments

#### Group Permissions by Module
```http
GET /permissions/by-module/
```

**Performance Features (T014)**:
- Response caching (5 minutes)
- Gzip compression
- Optimized aggregation queries

**Response Structure**:
```json
{
  "modules": [
    {
      "module": "users",
      "total_permissions": 15,
      "active_permissions": 14,
      "low_risk_count": 8,
      "medium_risk_count": 5,
      "high_risk_count": 2,
      "critical_risk_count": 0
    }
  ],
  "summary": {
    "total_modules": 8,
    "total_permissions": 150,
    "active_permissions": 145
  }
}
```

#### Permission Risk Analysis
```http
GET /permissions/risk-analysis/
```

**Performance Features (T014)**:
- Response caching (10 minutes)
- Gzip compression
- Optimized database queries

**Use Cases**:
- Security auditing and compliance
- Risk distribution analysis
- Over-privileged permission identification

### User Permissions Management

#### List User Permission Assignments
```http
GET /user-permissions/
```

**Query Parameters**:
- `user` (int): Filter by user ID
- `permission` (int): Filter by permission ID  
- `is_granted` (boolean): Filter by grant status

#### Grant Permission to User
```http
POST /user-permissions/
```

**Request Body**:
```json
{
  "user": 123,
  "permission": 45,
  "is_granted": true,
  "expires_at": "2024-12-31T23:59:59Z"
}
```

**Features**:
- Supports temporal permissions with expiration
- Validates permission compatibility
- Records complete audit trail

#### Revoke User Permission
```http
DELETE /user-permissions/{id}/
```

**Safety Features**:
- Cannot revoke system-critical permissions
- Records revocation reason in audit log
- Automatic notification to affected parties

#### Get Effective User Permissions
```http
GET /user-permissions/effective/{user_id}/
```

**Performance Features (T014)**:
- Response caching (3 minutes)
- Multi-level caching strategy
- Optimized permission resolution

**Response Structure**:
```json
{
  "user_id": 123,
  "username": "john_doe",
  "effective_permissions": {
    "direct_permissions": [
      {
        "id": 1,
        "name": "View Reports",
        "code": "reports.view",
        "source": "direct",
        "expires_at": "2024-12-31T23:59:59Z"
      }
    ],
    "group_permissions": [
      {
        "id": 2,
        "name": "Manage Users",
        "code": "users.manage", 
        "source": "group",
        "group_name": "Managers"
      }
    ],
    "last_updated": "2024-01-15T12:00:00Z"
  },
  "cached": true
}
```

### User Groups Management

#### List User Groups
```http
GET /groups/
```

**Query Parameters**:
- `is_active` (boolean): Filter by active status
- `group_type` (enum): Filter by type (`role`, `department`, `project`, `temporary`)

#### Create User Group
```http
POST /groups/
```

**Request Body**:
```json
{
  "name": "Project Managers",
  "description": "Managers for active projects",
  "group_type": "role",
  "is_active": true
}
```

#### Get Group Effective Permissions
```http
GET /groups/{id}/effective-permissions/
```

**Features**:
- Shows direct group permissions
- Includes inherited permissions from parent groups
- Resolves permission conflicts and precedence

### Performance Monitoring

#### API Performance Metrics
```http
GET /performance-metrics/
```

**T014 Performance Monitoring**:
- Response time statistics by endpoint
- Cache hit/miss ratios
- Database query performance
- Error rate monitoring

**Query Parameters**:
- `endpoint` (string): Filter by specific endpoint
- `time_range` (enum): Time range (`1h`, `24h`, `7d`, `30d`)

## Error Handling

All API endpoints follow RFC 7807 Problem Details format:

### Error Response Structure
```json
{
  "error": "Error category",
  "detail": "Human-readable description",
  "field_errors": {
    "field_name": ["Field-specific error messages"]
  }
}
```

### Common HTTP Status Codes

| Status | Description | Common Causes |
|--------|-------------|---------------|
| 200 | OK | Successful request |
| 201 | Created | Resource created successfully |
| 204 | No Content | Successful deletion |
| 400 | Bad Request | Invalid request data, validation errors |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict (duplicate codes) |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |

### Error Examples

#### Validation Error (400)
```json
{
  "error": "Validation failed",
  "detail": "The provided data is invalid",
  "field_errors": {
    "name": ["This field is required."],
    "risk_level": ["Invalid choice: 'invalid'. Choose from: low, medium, high, critical."]
  }
}
```

#### Authentication Error (401)
```json
{
  "error": "Authentication required",
  "detail": "Please provide valid authentication credentials"
}
```

#### Permission Error (403)
```json
{
  "error": "Insufficient permissions",
  "detail": "You do not have permission to perform this action"
}
```

## Rate Limiting

API endpoints are rate-limited to ensure system stability:

- **Authenticated users**: 1000 requests per hour
- **Anonymous users**: 100 requests per hour  
- **Administrative operations**: 500 requests per hour

Rate limit headers are included in all responses:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Performance Optimization (T014)

### Response Caching
- **List endpoints**: 5-minute cache
- **Detail endpoints**: 10-minute cache
- **Analytics endpoints**: 10-minute cache  
- **User permissions**: 3-minute cache

### Cache Headers
```http
Cache-Control: public, max-age=300
ETag: "abc123def456"
Vary: Accept-Encoding, Authorization
```

### Compression
All responses support gzip compression:
```http
Accept-Encoding: gzip, deflate
```

### Database Optimization
- Query optimization with `select_related()` and `prefetch_related()`
- Connection pooling with `CONN_MAX_AGE`
- Optimized pagination for large datasets

## API Versioning

### Current Version
- **Version**: v1
- **URL Pattern**: `/api/v1/`

### Versioning Strategy
- **URL Path Versioning**: Version specified in URL path
- **Backward Compatibility**: Maintained for 6 months minimum
- **Deprecation Notice**: 6 months advance notice for breaking changes

### Version Migration Paths

#### From v1.0 to v1.1 (Future)
- New optional fields added
- No breaking changes
- Automatic compatibility

#### Breaking Changes (v2.0 - Future)
When v2.0 is released:
1. **Preparation Phase** (3 months before): v2.0 endpoints available alongside v1
2. **Migration Phase** (3 months): Gradual migration with dual support  
3. **Deprecation Phase**: v1 marked deprecated with sunset date
4. **Sunset**: v1 endpoints removed

### Migration Checklist
- [ ] Review API changelog for breaking changes
- [ ] Test new endpoints in staging environment
- [ ] Update client applications
- [ ] Monitor error rates during migration
- [ ] Update authentication tokens if required

## Security Considerations

### Authentication Security
- Use HTTPS in production
- Rotate authentication tokens regularly
- Implement proper session management

### Permission Security
- Follow principle of least privilege
- Regularly audit high-risk permissions
- Monitor for privilege escalation attempts

### Data Security
- Sanitize all input parameters
- Use parameterized queries (automatic in Django ORM)
- Validate file uploads if applicable

## Troubleshooting Guide

### Common Issues

#### Permission Denied (403)
**Symptoms**: User receives 403 Forbidden errors when accessing endpoints

**Troubleshooting Steps**:
1. Verify user has required permissions:
   ```http
   GET /user-permissions/effective/{user_id}/
   ```
2. Check group memberships and group permissions
3. Verify permission is active (`is_active=true`)
4. Check for expired temporal permissions

**Solution**: Grant appropriate permissions or update group memberships

#### Performance Issues
**Symptoms**: Slow API response times, timeouts

**Troubleshooting Steps**:
1. Check performance metrics:
   ```http
   GET /performance-metrics/?time_range=1h
   ```
2. Monitor cache hit rates
3. Review database query patterns
4. Check server resource utilization

**Solution**: 
- Enable response caching
- Optimize database queries
- Increase server resources
- Review pagination settings

#### Authentication Failures  
**Symptoms**: 401 Unauthorized errors, invalid token messages

**Troubleshooting Steps**:
1. Verify token format: `Authorization: Token <token>`
2. Check token expiration
3. Validate user account is active
4. Review authentication logs

**Solution**:
- Generate new authentication token
- Activate user account if disabled
- Check for correct header format

#### Cache Issues
**Symptoms**: Stale data returned, inconsistent responses

**Troubleshooting Steps**:
1. Check cache configuration
2. Verify cache invalidation triggers
3. Review cache timeout settings
4. Clear cache manually if needed

**Solution**:
- Update cache invalidation logic
- Adjust cache timeouts
- Implement cache warming

### Debug Mode

For development environments, enable debug mode by adding query parameter:
```http
?debug=true
```

This provides additional response metadata:
```json
{
  "data": { /* normal response */ },
  "debug": {
    "query_count": 3,
    "cache_hits": ["permissions_list"],
    "response_time_ms": 145
  }
}
```

### Monitoring Endpoints

#### Health Check
```http
GET /health/
```

#### System Status  
```http
GET /status/
```

#### Performance Metrics
```http
GET /performance-metrics/
```

## Code Examples

### JavaScript/Fetch
```javascript
// Get permissions with authentication
const response = await fetch('/api/permissions/', {
  headers: {
    'Authorization': 'Token your-token-here',
    'Content-Type': 'application/json'
  }
});

const data = await response.json();
console.log(data.results);
```

### Python/Requests
```python
import requests

# Configure session with authentication
session = requests.Session()
session.headers.update({
    'Authorization': 'Token your-token-here',
    'Content-Type': 'application/json'
})

# Get user effective permissions
response = session.get('/api/user-permissions/effective/123/')
permissions = response.json()
```

### cURL
```bash
# List permissions with filtering
curl -H "Authorization: Token your-token-here" \
     "https://api.atalaiaspintas.com/api/permissions/?module=users&risk_level=high"

# Create new permission
curl -X POST \
     -H "Authorization: Token your-token-here" \
     -H "Content-Type: application/json" \
     -d '{"name":"Test Permission","code":"test.permission","module":"test","risk_level":"medium"}' \
     "https://api.atalaiaspintas.com/api/permissions/"
```

## Support and Resources

### Documentation
- **API Reference**: This document
- **OpenAPI Specification**: Available at `/api/schema/`
- **Interactive Documentation**: Available at `/api/docs/`

### Support Channels
- **Technical Support**: technical-support@atalaiaspintas.com
- **Issue Tracking**: GitHub Issues
- **Emergency Support**: +55 (XX) XXXX-XXXX

### Development Resources
- **Postman Collection**: Available for download
- **SDK Libraries**: Python, JavaScript (coming soon)
- **Code Examples**: GitHub repository

### SLA and Availability
- **Uptime Target**: 99.9%
- **Response Time Target**: < 200ms (95th percentile)
- **Support Response**: < 4 hours (business hours)

---

**Last Updated**: 2024-04-12  
**API Version**: 1.0.0  
**Documentation Version**: 1.0
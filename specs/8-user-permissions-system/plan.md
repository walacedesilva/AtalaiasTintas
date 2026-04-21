# Technical Implementation Plan: User Permissions System

**Feature**: `8-user-permissions-system`  
**Created**: 2026-04-18  
**Planning Phase**: Technical Architecture & Implementation Strategy

## Architecture Overview

### System Design Principles
- **Hierarchical Permission Model**: Leverage existing `User` boolean permissions as module-level gates, add granular sub-permissions for actions
- **Role-Based Access Control (RBAC)**: Implement groups with inherited permissions for easier administration
- **Real-time Permission Checking**: Middleware-based validation with caching for performance
- **Comprehensive Audit Trail**: All permission-related actions logged with full context
- **Backward Compatibility**: Maintain existing authentication while adding granular controls

### Core Components
1. **Permission Models**: Extended permission system with groups, roles, and audit
2. **Middleware Stack**: Permission validation and session management
3. **Administrative Interface**: Django admin extensions for permission management
4. **API Layer**: RESTful endpoints for permission CRUD operations
5. **Audit System**: Comprehensive logging and reporting infrastructure

## Database Schema Design

### New Models

#### `UserGroup` Model
```python
# apps/core/models.py extension
class UserGroup(TimeStampedModel):
    """Groups for organizing users with shared permissions"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # Hierarchical groups support
    parent_group = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        related_name='child_groups'
    )
    
    # Status and metadata
    is_active = models.BooleanField(default=True)
    system_group = models.BooleanField(default=False)  # Protected system groups
    
    # Auto-assignment rules
    auto_assign_new_users = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'auth_user_group'
```

#### `Permission` Model  
```python
class Permission(TimeStampedModel):
    """Granular permissions for specific actions/resources"""
    
    PERMISSION_TYPES = [
        ('module', 'Module Access'),      # High-level module access 
        ('action', 'Specific Action'),    # Granular action permissions
        ('data', 'Data Access Level'),    # Data visibility permissions
    ]
    
    # Core permission data
    name = models.CharField(max_length=100, unique=True)  # 'tintometry.formula.edit'
    display_name = models.CharField(max_length=200)       # 'Editar Fórmulas Tintométricas'
    description = models.TextField()
    permission_type = models.CharField(max_length=20, choices=PERMISSION_TYPES)
    
    # Categorization
    module = models.CharField(max_length=50)              # 'tintometry', 'sales', etc.
    resource = models.CharField(max_length=50)            # 'formula', 'discount', etc.
    action = models.CharField(max_length=20)              # 'view', 'edit', 'approve'
    
    # Constraints and metadata
    requires_approval = models.BooleanField(default=False)
    risk_level = models.CharField(max_length=20, choices=[
        ('low', 'Baixo Risco'),
        ('medium', 'Médio Risco'), 
        ('high', 'Alto Risco'),
        ('critical', 'Crítico')
    ])
    
    class Meta:
        db_table = 'auth_permission_extended'
```

#### `UserPermission` Model (Individual Permissions)
```python
class UserPermission(TimeStampedModel):
    """Direct user permissions (overrides group permissions)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    
    # Permission state
    granted = models.BooleanField(default=True)          # True=grant, False=explicit deny
    
    # Temporal permissions
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Context and approval
    granted_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='permissions_granted'
    )
    justification = models.TextField()
    approval_required = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'auth_user_permission'
        unique_together = ['user', 'permission']
```

#### `GroupPermission` Model
```python
class GroupPermission(TimeStampedModel):
    """Group-level permissions"""
    group = models.ForeignKey(UserGroup, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    
    # Permission context
    granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        db_table = 'auth_group_permission'
        unique_together = ['group', 'permission']
```

#### `UserGroupMembership` Model
```python
class UserGroupMembership(TimeStampedModel):
    """Many-to-many relationship between users and groups"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(UserGroup, on_delete=models.CASCADE)
    
    # Membership details
    assigned_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='group_assignments'
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'auth_user_group_membership'
        unique_together = ['user', 'group']
```

#### `PermissionAuditLog` Model
```python
class PermissionAuditLog(TimeStampedModel):
    """Comprehensive audit trail for all permission-related actions"""
    
    ACTION_TYPES = [
        ('permission_check', 'Verificação de Permissão'),
        ('permission_granted', 'Permissão Concedida'),
        ('permission_denied', 'Permissão Negada'),
        ('permission_revoked', 'Permissão Revogada'),
        ('group_assignment', 'Atribuição de Grupo'),
        ('group_removal', 'Remoção de Grupo'),
        ('login_success', 'Login Bem-sucedido'),
        ('login_failed', 'Tentativa de Login'),
        ('access_denied', 'Acesso Negado'),
    ]
    
    # Core audit data
    action_type = models.CharField(max_length=30, choices=ACTION_TYPES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    permission = models.ForeignKey(Permission, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Action context
    resource_accessed = models.CharField(max_length=200, blank=True)    # URL or resource identifier
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    
    # Action details
    success = models.BooleanField(default=True)
    failure_reason = models.TextField(blank=True)
    additional_data = models.JSONField(default=dict, blank=True)        # Flexible data storage
    
    class Meta:
        db_table = 'auth_permission_audit'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action_type', 'created_at']),
            models.Index(fields=['ip_address', 'created_at']),
        ]
```

### User Model Extensions
```python
# Extend existing User model with permission methods
class User(AbstractUser):
    # ... existing fields ...
    
    # Permission-related methods
    def has_module_access(self, module_name):
        """Check if user has access to a module (high-level check)"""
        
    def has_permission(self, permission_name):
        """Check granular permission with caching"""
        
    def get_effective_permissions(self):
        """Get all permissions (direct + inherited from groups)"""
        
    def get_groups(self):
        """Get all groups user belongs to"""
        
    def assign_to_group(self, group, assigned_by=None, expires_at=None):
        """Add user to group with audit trail"""
        
    def remove_from_group(self, group, removed_by=None):
        """Remove user from group with audit trail"""
```

## API Layer Design

### Permission Management Endpoints

#### Core Permission APIs
```python
# apps/core/views.py - Permission ViewSets

class PermissionViewSet(viewsets.ModelViewSet):
    """CRUD operations for permissions"""
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [IsAuthenticated, HasPermission('core.permission.manage')]
    
    @action(detail=False, methods=['get'])
    def by_module(self, request):
        """Get permissions grouped by module"""
        
    @action(detail=False, methods=['get']) 
    def risk_analysis(self, request):
        """Get permissions by risk level"""

class UserGroupViewSet(viewsets.ModelViewSet):
    """Group management endpoints"""
    queryset = UserGroup.objects.all()
    serializer_class = UserGroupSerializer
    permission_classes = [IsAuthenticated, HasPermission('core.group.manage')]
    
    @action(detail=True, methods=['post'])
    def assign_users(self, request, pk=None):
        """Assign multiple users to group"""
        
    @action(detail=True, methods=['post'])
    def assign_permissions(self, request, pk=None):
        """Assign multiple permissions to group"""
        
    @action(detail=True, methods=['get'])
    def effective_permissions(self, request, pk=None):
        """Get all effective permissions for group"""

class UserPermissionViewSet(viewsets.ModelViewSet):
    """Individual user permission management"""
    queryset = UserPermission.objects.all()
    serializer_class = UserPermissionSerializer
    permission_classes = [IsAuthenticated, HasPermission('core.user_permission.manage')]
    
    @action(detail=False, methods=['post'])
    def bulk_assign(self, request):
        """Bulk assign permissions to users"""
        
    @action(detail=False, methods=['delete'])
    def bulk_revoke(self, request):
        """Bulk revoke permissions"""
```

#### User Management Extensions
```python
class UserManagementViewSet(viewsets.GenericViewSet):
    """Extended user management with permissions"""
    
    @action(detail=True, methods=['get'])
    def permission_summary(self, request, pk=None):
        """Get comprehensive permission summary for user"""
        
    @action(detail=True, methods=['post'])
    def delegate_permissions(self, request, pk=None):
        """Temporary permission delegation"""
        
    @action(detail=True, methods=['get'])
    def audit_trail(self, request, pk=None):
        """Get permission-related audit trail for user"""
        
    @action(detail=False, methods=['post'])
    def simulate_permissions(self, request):
        """Simulate permission set for testing"""
```

#### Audit and Reporting APIs
```python
class PermissionAuditViewSet(viewsets.ReadOnlyModelViewSet):
    """Audit trail and reporting"""
    queryset = PermissionAuditLog.objects.all()
    serializer_class = PermissionAuditSerializer
    permission_classes = [IsAuthenticated, HasPermission('core.audit.view')]
    
    @action(detail=False, methods=['get'])
    def security_report(self, request):
        """Generate security usage report"""
        
    @action(detail=False, methods=['get'])
    def access_patterns(self, request):
        """Analyze user access patterns"""
        
    @action(detail=False, methods=['get'])
    def risk_analysis(self, request):
        """Identify high-risk activities"""
```

## Middleware Implementation

### Permission Validation Middleware
```python
# apps/core/middleware.py

class PermissionValidationMiddleware:
    """Real-time permission checking for all requests"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Cache for URL-permission mapping
        self.url_permission_map = self._build_url_permission_map()
    
    def __call__(self, request):
        # Skip for public URLs and admin
        if self._should_skip_validation(request):
            return self.get_response(request)
            
        # Validate permissions
        if not self._check_user_permissions(request):
            return self._handle_permission_denied(request)
            
        # Log access for audit
        self._log_access_attempt(request, success=True)
        
        response = self.get_response(request)
        return response
    
    def _check_user_permissions(self, request):
        """Core permission validation logic"""
        
    def _build_url_permission_map(self):
        """Build mapping of URLs to required permissions"""
        
    def _handle_permission_denied(self, request):
        """Handle permission denied scenarios"""
```

### Session Management Middleware  
```python
class EnhancedSessionMiddleware:
    """Enhanced session management with permission context"""
    
    def __call__(self, request):
        # Add permission context to session
        if request.user.is_authenticated:
            self._populate_session_permissions(request)
            self._check_session_expiry(request)
            
        return self.get_response(request)
    
    def _populate_session_permissions(self, request):
        """Cache user permissions in session for performance"""
        
    def _check_session_expiry(self, request):
        """Handle inactivity-based session expiry"""
```

## Frontend Integration

### Permission Context Provider
```typescript
// frontend/src/providers/PermissionProvider.tsx

interface PermissionContextType {
  permissions: string[];
  hasPermission: (permission: string) => boolean;
  hasModuleAccess: (module: string) => boolean;
  checkMultiplePermissions: (permissions: string[]) => boolean;
  isLoading: boolean;
}

export const PermissionProvider: React.FC<{children: ReactNode}> = ({children}) => {
  const [permissions, setPermissions] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  
  // Load user permissions on mount
  useEffect(() => {
    loadUserPermissions();
  }, []);
  
  const hasPermission = (permission: string): boolean => {
    return permissions.includes(permission);
  };
  
  // ... implementation details
};
```

### Permission-Based Components
```typescript
// frontend/src/components/PermissionGuard.tsx

interface PermissionGuardProps {
  permission: string | string[];
  children: ReactNode;
  fallback?: ReactNode;
  requireAll?: boolean; // For multiple permissions
}

export const PermissionGuard: React.FC<PermissionGuardProps> = ({
  permission,
  children,
  fallback = null,
  requireAll = false
}) => {
  const { hasPermission, checkMultiplePermissions } = usePermissions();
  
  const hasAccess = Array.isArray(permission)
    ? checkMultiplePermissions(permission)
    : hasPermission(permission);
    
  return hasAccess ? <>{children}</> : <>{fallback}</>;
};
```

## Administrative Interface

### Django Admin Extensions
```python
# apps/core/admin.py

class UserPermissionInline(admin.TabularInline):
    """Inline for individual user permissions"""
    model = UserPermission
    extra = 0
    readonly_fields = ['granted_by', 'created_at']

class UserGroupMembershipInline(admin.TabularInline):
    """Inline for group memberships"""
    model = UserGroupMembership
    extra = 0

@admin.register(User)
class UserAdminExtended(admin.ModelAdmin):
    """Enhanced user admin with permission management"""
    
    list_display = [
        'username', 'email', 'first_name', 'last_name', 
        'is_active', 'permission_count', 'group_count'
    ]
    
    list_filter = [
        'is_active', 'is_staff', 'groups__name',
        'userpermission__permission__module'
    ]
    
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    inlines = [UserPermissionInline, UserGroupMembershipInline]
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Legacy Permissions', {
            'fields': ('pode_vender', 'pode_gerenciar_estoque', 
                      'pode_acessar_financeiro', 'pode_administrar'),
            'description': 'Permissões legado - mantidas para compatibilidade'
        }),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    
    def permission_count(self, obj):
        return obj.userpermission_set.filter(granted=True).count()
    permission_count.short_description = 'Permissões'
    
    def group_count(self, obj):
        return obj.usergroupmembership_set.count()
    group_count.short_description = 'Grupos'

@admin.register(UserGroup)
class UserGroupAdmin(admin.ModelAdmin):
    """Group management in admin"""
    
    list_display = ['name', 'description', 'is_active', 'member_count', 'permission_count']
    list_filter = ['is_active', 'system_group', 'parent_group']
    search_fields = ['name', 'description']
    
    def member_count(self, obj):
        return obj.usergroupmembership_set.count()
    
    def permission_count(self, obj):
        return obj.grouppermission_set.count()

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    """Permission management"""
    
    list_display = ['name', 'display_name', 'module', 'resource', 'action', 'risk_level']
    list_filter = ['module', 'permission_type', 'risk_level', 'requires_approval']
    search_fields = ['name', 'display_name', 'description']
    
    fieldsets = (
        (None, {'fields': ('name', 'display_name', 'description')}),
        ('Classification', {'fields': ('permission_type', 'module', 'resource', 'action')}),
        ('Security', {'fields': ('risk_level', 'requires_approval')}),
    )
```

### Custom Permission Management Interface
```python
# apps/core/admin_views.py

class PermissionMatrixView(admin.ModelAdmin):
    """Matrix view for managing user-permission relationships"""
    change_list_template = 'admin/permission_matrix.html'
    
    def changelist_view(self, request, extra_context=None):
        # Build permission matrix data
        users = User.objects.filter(is_active=True)
        permissions = Permission.objects.order_by('module', 'resource', 'action')
        
        matrix_data = self._build_matrix_data(users, permissions)
        
        extra_context = extra_context or {}
        extra_context.update({
            'matrix_data': matrix_data,
            'users': users,
            'permissions': permissions,
        })
        
        return super().changelist_view(request, extra_context)
    
    def _build_matrix_data(self, users, permissions):
        """Build the permission matrix for display"""
        # Implementation for matrix data structure
```

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1-2)
**Dependencies**: None  
**Scope**: Database models and basic API framework

**Tasks**:
- Create new models (UserGroup, Permission, UserPermission, etc.)
- Generate and run database migrations
- Implement basic model methods and managers
- Create serializers for API layer
- Set up basic unit tests

**Deliverables**:
- Working database schema
- Basic CRUD operations via Django admin
- Core model tests passing

### Phase 2: API Layer (Week 3-4)
**Dependencies**: Phase 1 complete  
**Scope**: RESTful endpoints and business logic

**Tasks**:  
- Implement PermissionViewSet and UserGroupViewSet
- Create permission checking utilities  
- Build audit logging infrastructure
- Implement caching layer for performance
- Add comprehensive API tests

**Deliverables**:
- Complete API endpoints documented and tested
- Permission validation utilities
- Audit system operational

### Phase 3: Middleware Integration (Week 5)
**Dependencies**: Phase 2 complete  
**Scope**: Real-time permission validation

**Tasks**:
- Implement PermissionValidationMiddleware
- Create URL-permission mapping system
- Add session-based permission caching
- Handle permission denied scenarios gracefully
- Integration testing with existing system

**Deliverables**:
- Middleware protecting non-ERP screens
- Performance benchmarks showing <100ms validation
- Integration tests with existing auth

### Phase 4: Administrative Interface (Week 6)
**Dependencies**: Phase 3 complete  
**Scope**: User-friendly admin tools

**Tasks**:
- Extend Django admin for permission management  
- Create permission matrix view
- Implement bulk operations (assign/revoke permissions)
- Add user search and filtering
- Create audit reporting interface

**Deliverables**:
- Complete admin interface for permission management
- Bulk operations functional and tested
- Admin user training documentation

### Phase 5: Frontend Integration (Week 7-8)
**Dependencies**: Phase 4 complete  
**Scope**: React/TypeScript permission components

**Tasks**:
- Create PermissionProvider context
- Implement PermissionGuard components
- Add permission-based navigation
- Integrate with existing frontend auth
- Add frontend permission caching

**Deliverables**:
- Permission-aware React components
- Seamless integration with existing UI
- Frontend performance optimization

### Phase 6: Testing & Hardening (Week 9)
**Dependencies**: Phase 5 complete  
**Scope**: Security testing and optimization

**Tasks**:
- Comprehensive security testing
- Performance optimization and caching
- Load testing with concurrent users
- Penetration testing of permission bypasses
- Documentation and training materials

**Deliverables**:
- Security audit report
- Performance benchmarks
- User documentation and training guides

## Security Considerations

### Permission Bypass Prevention
- **Double Authorization**: Check permissions both in middleware and view level
- **SQL Injection Protection**: Use parameterized queries for permission checks
- **Session Hijacking**: Validate session integrity and IP consistency  
- **Privilege Escalation**: Audit all permission assignments requiring approval
- **Cache Poisoning**: Secure permission cache with proper invalidation

### Data Protection
- **Sensitive Data Access**: Log all access to financial and formula data
- **Data Export Controls**: Restrict bulk data export permissions
- **Field-Level Security**: Protect sensitive fields in serializers based on permissions
- **API Rate Limiting**: Prevent brute force permission probing

### Audit Requirements
- **Immutable Logs**: Audit logs protected from modification or deletion
- **Complete Traceability**: Every permission check and change logged
- **Real-time Monitoring**: Alerts for suspicious permission activities
- **Compliance Reporting**: Automated reports for audit requirements

## Performance Optimization

### Caching Strategy
```python
# Permission caching implementation
class PermissionCache:
    """Redis-based permission caching"""
    
    def get_user_permissions(self, user_id):
        cache_key = f"user_perms:{user_id}"
        cached = cache.get(cache_key)
        
        if cached is None:
            permissions = self._load_user_permissions(user_id)
            cache.set(cache_key, permissions, timeout=300)  # 5 minutes
            return permissions
            
        return cached
    
    def invalidate_user_cache(self, user_id):
        cache_key = f"user_perms:{user_id}"
        cache.delete(cache_key)
    
    def invalidate_group_cache(self, group_id):
        # Invalidate all users in the group
        group_members = UserGroupMembership.objects.filter(group_id=group_id)
        for membership in group_members:
            self.invalidate_user_cache(membership.user_id)
```

### Database Optimization
- **Indexes**: Strategic indexes on frequently queried fields
- **Query Optimization**: Use select_related and prefetch_related for permission queries
- **Connection Pooling**: Configure proper database connection pooling
- **Read Replicas**: Use read replicas for audit queries if needed

### API Performance  
- **Pagination**: All list endpoints properly paginated
- **Field Selection**: Allow clients to specify which fields to return
- **Compression**: Enable gzip compression for API responses
- **HTTP Caching**: Proper cache headers for permission data

## Migration Strategy

### Data Migration Plan
1. **Phase 1**: Create new tables alongside existing system
2. **Phase 2**: Migrate existing users maintaining current boolean permissions
3. **Phase 3**: Create default groups based on existing permission patterns
4. **Phase 4**: Gradually transition screens to use new permission system
5. **Phase 5**: Deprecate old boolean fields (maintain for compatibility)

### Rollback Strategy
- Maintain existing authentication system during implementation
- Feature flags for enabling/disabling new permission system
- Database snapshots before each migration phase
- Quick rollback procedures documented and tested

## Testing Strategy

### Unit Testing
- 100% coverage for permission checking logic
- Mock external dependencies (cache, database)
- Test edge cases (expired permissions, deleted users, etc.)
- Performance tests for permission validation (<100ms requirement)

### Integration Testing  
- Test middleware integration with Django request flow
- Validate API endpoints with various permission scenarios
- Test admin interface functionality
- Cross-browser compatibility testing

### Security Testing
- Automated security scans for common vulnerabilities
- Manual penetration testing for permission bypasses
- Load testing to identify performance bottlenecks
- Audit trail integrity testing

### User Acceptance Testing
- Admin user workflow testing (create groups, assign permissions)
- End user experience testing (clear error messages, intuitive interface)
- Performance testing with realistic user loads
- Training effectiveness validation

## Monitoring and Maintenance

### Key Metrics
- Permission validation response time (target: <100ms)
- Failed permission attempts (security monitoring)
- User satisfaction scores (usability)
- System availability (target: >99.5%)

### Alerting
- Failed login attempts exceeding threshold
- Unusual permission assignment patterns
- Performance degradation alerts
- Audit log integrity checks

### Documentation
- API documentation with examples
- Administrative procedures manual
- Security policy documentation  
- User training materials

This technical plan provides a comprehensive roadmap for implementing the user permissions system while maintaining system reliability, security, and performance standards.
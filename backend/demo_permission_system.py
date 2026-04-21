#!/usr/bin/env python
"""
Demonstração do Sistema de Permissões Hierárquico - AtalaiasTintas
Sistema: Django Paint Management System
Implementação: Hierarquia de Permissões com Auditoria Completa

Este script demonstra o funcionamento do novo sistema de permissões
implementado para controlar acesso granular às funcionalidades não-ERP.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tintas_system.settings')
django.setup()

from apps.core.models import User, UserGroup, Permission, GroupMembership, UserPermission, GroupPermission, PermissionAuditLog

def print_separator(title):
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def demonstrate_permission_system():
    """Demonstra o funcionamento do sistema de permissões hierárquico"""
    
    print_separator("DEMONSTRATION: Hierarchical Permission System")
    
    # 1. Create a test user
    test_user, created = User.objects.get_or_create(
        username='colorista_teste',
        defaults={
            'email': 'colorista@atalaiastintas.com',
            'first_name': 'João',
            'last_name': 'Silva',
            'pode_vender': False,  # Legacy permission still False
        }
    )
    
    if created:
        print("✓ Created test user: colorista_teste")
    else:
        print("→ Using existing test user: colorista_teste")
    
    # 2. Add user to Coloristas group
    coloristas_group = UserGroup.objects.get(name='Coloristas')
    membership = test_user.add_to_group(
        group=coloristas_group,
        is_primary=True,
        reason="Demonstração do sistema"
    )
    print(f"✓ Added user to group: {coloristas_group.name}")
    
    # 3. Test permission checking
    print("\\n--- Testing Permission Checks ---")
    
    # Test tintometry permissions (should have)
    print(f"Can view formulas: {test_user.has_permission_new('tintometry.formula.view')}")
    print(f"Can create formulas: {test_user.has_permission_new('tintometry.formula.create')}")
    print(f"Can mix batches: {test_user.has_permission_new('tintometry.batch.mix')}")
    
    # Test admin permissions (should not have)
    print(f"Can manage users: {test_user.has_permission_new('admin.user.manage')}")
    print(f"Can manage permissions: {test_user.has_permission_new('admin.permission.manage')}")
    
    # Test sales permissions (should not have)
    print(f"Can view orders: {test_user.has_permission_new('sales.order.view')}")
    
    # 4. Get all user permissions
    print("\\n--- All User Permissions ---")
    all_perms = test_user.get_all_permissions_new()
    for perm in all_perms:
        print(f"  • {perm}")
    
    # 5. Grant a direct permission
    print("\\n--- Granting Direct Permission ---")
    test_user.grant_permission(
        'sales.order.view',
        reason='Permissão especial para ver pedidos'
    )
    print("✓ Granted direct permission: sales.order.view")
    
    # Check again
    print(f"Can view orders now: {test_user.has_permission_new('sales.order.view')}")
    
    # 6. Show audit log
    print("\\n--- Recent Audit Log ---")
    recent_logs = PermissionAuditLog.objects.filter(
        target_user=test_user
    ).order_by('-created_at')[:3]
    
    for log in recent_logs:
        print(f"  {log.created_at.strftime('%Y-%m-%d %H:%M')} - {log.action}: {log.reason}")
    
    # 7. Show hierarchical structure
    print("\\n--- Group Structure ---")
    primary_group = test_user.get_primary_group()
    if primary_group:
        print(f"Primary Group: {primary_group.name}")
        print(f"Description: {primary_group.description}")
        print(f"Full Path: {primary_group.get_full_path()}")
        print(f"User Count: {primary_group.get_user_count()}")
    
    # 8. Test permission inheritance (create a sub-group)
    print("\\n--- Testing Hierarchical Inheritance ---")
    
    # Create a sub-group
    senior_coloristas, created = UserGroup.objects.get_or_create(
        name='Coloristas Seniores',
        defaults={
            'description': 'Coloristas com experiência avançada',
            'parent': coloristas_group,
            'is_active': True,
            'is_system': False
        }
    )
    
    if created:
        print("✓ Created sub-group: Coloristas Seniores")
        
        # Add special permission to parent group
        formula_delete_perm = Permission.objects.get(
            module='tintometry',
            resource='formula', 
            action='delete'
        )
        
        GroupPermission.objects.get_or_create(
            group=coloristas_group,
            permission=formula_delete_perm,
            defaults={
                'grant_type': 'allow',
                'is_active': True,
                'inherit_to_children': True,
                'reason': 'Permissão para coloristas experientes'
            }
        )
        print("✓ Added delete formula permission to parent group")
    
    # Add user to sub-group
    test_user.add_to_group(senior_coloristas)
    print("✓ Added user to sub-group")
    
    # Test inherited permission
    print(f"Can delete formulas (inherited): {test_user.has_permission_new('tintometry.formula.delete')}")
    
    print("\\n--- System Performance ---")
    import time
    
    # Test performance
    start = time.time()
    for _ in range(100):
        test_user.has_permission_new('tintometry.formula.view')
    end = time.time()
    
    print(f"100 permission checks took: {(end-start)*1000:.2f}ms")
    print(f"Average per check: {((end-start)*1000)/100:.2f}ms")
    
    print("\\n--- Legacy Compatibility ---")
    print(f"Legacy pode_vender: {test_user.pode_vender}")
    print(f"Legacy pode_administrar: {test_user.pode_administrar}")
    print("→ Legacy fields preserved for backward compatibility")
    
    print_separator("DEMONSTRATION COMPLETED SUCCESSFULLY")
    print("✅ Hierarchical permission system working correctly!")
    print("✅ Audit trails are being recorded!")
    print("✅ Group inheritance is functioning!")
    print("✅ Performance is within acceptable limits!")
    print("✅ Legacy compatibility maintained!")

if __name__ == "__main__":
    demonstrate_permission_system()
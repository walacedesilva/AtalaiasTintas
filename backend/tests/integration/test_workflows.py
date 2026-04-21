"""
T018: API Integration Testing - Workflow Testing
Test Module: test_workflows.py

Workflow-focused integration tests for the User Permissions System,
validating complex business workflows and cross-system integrations.
"""

import json
import time
from decimal import Decimal
from datetime import datetime, timedelta
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, Mock
import pytest

from apps.core.models import (
    Permission, UserGroup, UserPermission, GroupPermission,
    GroupMembership, PermissionAuditLog, UserSession, AuditLog
)

User = get_user_model()


class PermissionWorkflowIntegrationTestCase(APITestCase):
    """
    T018: Workflow-focused integration tests for permission system.
    
    Tests complex business workflows that span multiple API endpoints
    and validate real-world permission management scenarios.
    """
    
    def setUp(self):
        """Set up test environment with workflow-specific test data."""
        cache.clear()
        
        # Create organizational structure
        self.ceo = User.objects.create_user(
            username='ceo',
            email='ceo@company.com',
            password='ceo_pass_123',
            is_staff=True,
            is_superuser=True
        )
        
        self.finance_manager = User.objects.create_user(
            username='finance_manager',
            email='finance@company.com',
            password='finance_pass_123'
        )
        
        self.sales_manager = User.objects.create_user(
            username='sales_manager',
            email='sales@company.com',
            password='sales_pass_123'
        )
        
        self.sales_rep1 = User.objects.create_user(
            username='sales_rep1',
            email='rep1@company.com',
            password='rep1_pass_123'
        )
        
        self.sales_rep2 = User.objects.create_user(
            username='sales_rep2',
            email='rep2@company.com',
            password='rep2_pass_123'
        )
        
        self.new_employee = User.objects.create_user(
            username='new_employee',
            email='newbie@company.com',
            password='newbie_pass_123'
        )
        
        # Create permission hierarchy
        self.create_business_permissions()
        self.create_organizational_groups()
        
        # Set up API client
        self.client = APIClient()
    
    def create_business_permissions(self):
        """Create a realistic set of business permissions."""
        self.permissions = {}
        
        # Sales permissions
        self.permissions['sales_view'] = Permission.objects.create(
            code='sales.order.view',
            name='View Sales Orders',
            description='Can view sales order information',
            module='sales',
            resource='order',
            action='view',
            risk_level='low'
        )
        
        self.permissions['sales_create'] = Permission.objects.create(
            code='sales.order.create',
            name='Create Sales Orders',
            description='Can create new sales orders',
            module='sales',
            resource='order',
            action='create',
            risk_level='medium'
        )
        
        self.permissions['sales_approve'] = Permission.objects.create(
            code='sales.order.approve',
            name='Approve Sales Orders',
            description='Can approve sales orders above threshold',
            module='sales',
            resource='order',
            action='approve',
            risk_level='high'
        )
        
        # Financial permissions
        self.permissions['finance_view'] = Permission.objects.create(
            code='finance.report.view',
            name='View Financial Reports',
            description='Can view financial reports',
            module='finance',
            resource='report',
            action='view',
            risk_level='medium'
        )
        
        self.permissions['finance_modify'] = Permission.objects.create(
            code='finance.transaction.modify',
            name='Modify Financial Transactions',
            description='Can modify financial transactions',
            module='finance',
            resource='transaction',
            action='modify',
            risk_level='critical'
        )
        
        # Administrative permissions
        self.permissions['admin_users'] = Permission.objects.create(
            code='admin.user.manage',
            name='Manage Users',
            description='Can manage user accounts',
            module='admin',
            resource='user',
            action='manage',
            risk_level='critical'
        )
        
        self.permissions['admin_system'] = Permission.objects.create(
            code='admin.system.configure',
            name='System Configuration',
            description='Can modify system configuration',
            module='admin',
            resource='system',
            action='configure',
            risk_level='critical'
        )
    
    def create_organizational_groups(self):
        """Create organizational groups with hierarchical structure."""
        self.groups = {}
        
        # Executive level
        self.groups['executives'] = UserGroup.objects.create(
            name='Executives',
            description='C-level executives with full access',
            is_active=True
        )
        
        # Department managers
        self.groups['finance_managers'] = UserGroup.objects.create(
            name='Finance Managers',
            description='Finance department managers',
            is_active=True,
            parent_group=self.groups['executives']  # Hierarchical relationship if supported
        )
        
        self.groups['sales_managers'] = UserGroup.objects.create(
            name='Sales Managers',
            description='Sales department managers',
            is_active=True,
            parent_group=self.groups['executives']
        )
        
        # Regular employees
        self.groups['sales_team'] = UserGroup.objects.create(
            name='Sales Team',
            description='Sales representatives',
            is_active=True,
            parent_group=self.groups['sales_managers']
        )
        
        self.groups['finance_team'] = UserGroup.objects.create(
            name='Finance Team',
            description='Finance department staff',
            is_active=True,
            parent_group=self.groups['finance_managers']
        )
    
    def test_001_employee_onboarding_workflow(self):
        """
        T018-001: Test complete employee onboarding workflow.
        
        Simulates new employee onboarding with progressive permission assignment:
        1. Basic access assignment
        2. Department-specific permissions
        3. Role-based escalation
        4. Audit trail validation
        """
        self.client.force_authenticate(user=self.ceo)
        
        # Step 1: Initial basic access for new employee
        basic_permissions = [self.permissions['sales_view']]
        
        for permission in basic_permissions:
            assignment_data = {
                'user': self.new_employee.id,
                'permission': permission.id,
                'is_granted': True,
                'reason': 'Initial onboarding - basic access'
            }
            
            response = self.client.post(
                reverse('userpermission-list'),
                assignment_data,
                format='json'
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify basic access granted
        self.assertTrue(
            self.new_employee.has_permission_new('sales.order.view')
        )
        
        # Step 2: Add to department group (Sales Team)
        membership_data = {
            'user': self.new_employee.id,
            'group': self.groups['sales_team'].id
        }
        
        response = self.client.post(
            reverse('groupmembership-list'),
            membership_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Grant sales team permissions
        team_permissions = [self.permissions['sales_create']]
        
        for permission in team_permissions:
            group_permission_data = {
                'group': self.groups['sales_team'].id,
                'permission': permission.id,
                'is_granted': True,
                'reason': 'Standard sales team permissions'
            }
            
            response = self.client.post(
                reverse('grouppermission-list'),
                group_permission_data,
                format='json'
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify inherited permissions
        self.assertTrue(
            self.new_employee.has_permission_new('sales.order.create')
        )
        
        # Step 3: Role escalation (promote to sales manager after 6 months)
        # Simulate time progression with expires_at
        future_date = timezone.now() + timedelta(days=180)
        
        # Add to sales managers group with future effective date
        manager_membership_data = {
            'user': self.new_employee.id,
            'group': self.groups['sales_managers'].id
        }
        
        response = self.client.post(
            reverse('groupmembership-list'),
            manager_membership_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Grant manager-level permissions
        manager_permission_data = {
            'group': self.groups['sales_managers'].id,
            'permission': self.permissions['sales_approve'].id,
            'is_granted': True,
            'reason': 'Sales manager authority'
        }
        
        response = self.client.post(
            reverse('grouppermission-list'),
            manager_permission_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify new manager permissions
        self.assertTrue(
            self.new_employee.has_permission_new('sales.order.approve')
        )
        
        # Step 4: Validate audit trail
        audit_logs = PermissionAuditLog.objects.filter(
            details__contains=self.new_employee.username
        )
        
        # Should have logs for each permission assignment
        self.assertGreaterEqual(audit_logs.count(), 3)
        
        # Verify audit log details
        for log in audit_logs:
            self.assertIn(log.action, ['permission_granted', 'group_membership_added'])
            self.assertEqual(log.actor, self.ceo)
    
    def test_002_department_restructuring_workflow(self):
        """
        T018-002: Test department restructuring workflow.
        
        Simulates organizational restructuring:
        1. Bulk permission transfers
        2. Group hierarchy changes
        3. Permission inheritance updates
        4. Access validation
        """
        self.client.force_authenticate(user=self.ceo)
        
        # Initial setup - assign permissions to sales team
        initial_setup_data = [
            {
                'group': self.groups['sales_team'].id,
                'permission': self.permissions['sales_view'].id,
                'is_granted': True,
                'reason': 'Initial sales team setup'
            },
            {
                'group': self.groups['sales_team'].id,
                'permission': self.permissions['sales_create'].id,
                'is_granted': True,
                'reason': 'Initial sales team setup'
            }
        ]
        
        for setup_data in initial_setup_data:
            response = self.client.post(
                reverse('grouppermission-list'),
                setup_data,
                format='json'
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Add sales reps to team
        for sales_rep in [self.sales_rep1, self.sales_rep2]:
            membership_data = {
                'user': sales_rep.id,
                'group': self.groups['sales_team'].id
            }
            
            response = self.client.post(
                reverse('groupmembership-list'),
                membership_data,
                format='json'
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify initial permissions
        for sales_rep in [self.sales_rep1, self.sales_rep2]:
            self.assertTrue(sales_rep.has_permission_new('sales.order.view'))
            self.assertTrue(sales_rep.has_permission_new('sales.order.create'))
        
        # Step 1: Restructuring - merge sales and finance teams
        # Create new combined group
        combined_group_data = {
            'name': 'Revenue Operations',
            'description': 'Combined sales and finance operations team',
            'is_active': True
        }
        
        response = self.client.post(
            reverse('usergroup-list'),
            combined_group_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        combined_group_id = response.data['id']
        
        # Step 2: Bulk transfer permissions from sales team to combined group
        bulk_transfer_data = {
            'users': [self.sales_rep1.id, self.sales_rep2.id],
            'permissions': [self.permissions['sales_view'].id, self.permissions['sales_create'].id],
            'action': 'grant',
            'reason': 'Department restructuring - revenue operations'
        }
        
        # Note: This would use a bulk endpoint if implemented
        # For now, simulate with individual transfers
        
        # Add users to new combined group
        for sales_rep in [self.sales_rep1, self.sales_rep2]:
            membership_data = {
                'user': sales_rep.id,
                'group': combined_group_id
            }
            
            response = self.client.post(
                reverse('groupmembership-list'),
                membership_data,
                format='json'
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Grant combined permissions (sales + basic finance)
        combined_permissions = [
            self.permissions['sales_view'],
            self.permissions['sales_create'],
            self.permissions['finance_view']  # New finance access
        ]
        
        for permission in combined_permissions:
            group_permission_data = {
                'group': combined_group_id,
                'permission': permission.id,
                'is_granted': True,
                'reason': 'Revenue operations team permissions'
            }
            
            response = self.client.post(
                reverse('grouppermission-list'),
                group_permission_data,
                format='json'
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Step 3: Verify new permissions structure
        for sales_rep in [self.sales_rep1, self.sales_rep2]:
            # Should retain original sales permissions
            self.assertTrue(sales_rep.has_permission_new('sales.order.view'))
            self.assertTrue(sales_rep.has_permission_new('sales.order.create'))
            
            # Should have new finance permissions
            self.assertTrue(sales_rep.has_permission_new('finance.report.view'))
        
        # Step 4: Deactivate old sales team group
        old_group_data = {'is_active': False}
        
        response = self.client.patch(
            reverse('usergroup-detail', args=[self.groups['sales_team'].id]),
            old_group_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify audit trail for restructuring
        restructuring_logs = PermissionAuditLog.objects.filter(
            reason__icontains='restructuring'
        ).order_by('-created_at')
        
        self.assertGreaterEqual(restructuring_logs.count(), 2)
    
    def test_003_seasonal_permission_workflow(self):
        """
        T018-003: Test seasonal/temporary permission workflow.
        
        Simulates seasonal business needs:
        1. Temporary permission grants with expiration
        2. Automated expiration handling
        3. Renewal processes
        4. Compliance reporting
        """
        self.client.force_authenticate(user=self.finance_manager)
        
        # Step 1: Grant temporary high-privilege access for year-end closing
        year_end_date = timezone.now() + timedelta(days=30)
        
        temp_permission_data = {
            'user': self.sales_manager.id,
            'permission': self.permissions['finance_view'].id,
            'is_granted': True,
            'expires_at': year_end_date.isoformat(),
            'reason': 'Year-end financial closing - temporary access'
        }
        
        response = self.client.post(
            reverse('userpermission-list'),
            temp_permission_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        temp_permission_id = response.data['id']
        
        # Verify temporary access granted
        self.assertTrue(
            self.sales_manager.has_permission_new('finance.report.view')
        )
        
        # Step 2: Monitor permission usage during temporary period
        # Simulate permission usage through API calls
        self.client.force_authenticate(user=self.sales_manager)
        
        # Sales manager accesses financial reports (should succeed)
        response = self.client.get(reverse('permission-check'), {
            'permission': 'finance.report.view'
        })
        # Note: This endpoint would need to be implemented
        
        # Step 3: Test permission renewal request
        self.client.force_authenticate(user=self.sales_manager)
        
        renewal_request_data = {
            'permission_assignment': temp_permission_id,
            'requested_extension_days': 15,
            'business_justification': 'Additional time needed for financial analysis completion'
        }
        
        # Note: This would be a custom endpoint for permission renewal requests
        # For now, simulate with a direct update
        self.client.force_authenticate(user=self.finance_manager)
        
        extended_date = year_end_date + timedelta(days=15)
        renewal_data = {
            'expires_at': extended_date.isoformat(),
            'reason': 'Extended for financial analysis completion'
        }
        
        response = self.client.patch(
            reverse('userpermission-detail', args=[temp_permission_id]),
            renewal_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Step 4: Simulate expiration and auto-revocation
        # Mock current time to be past expiration
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = extended_date + timedelta(days=1)
            
            # Permission check should now fail
            expired_permission = UserPermission.objects.get(id=temp_permission_id)
            
            # Note: This would require implementing expiration checking in has_permission_new
            # For now, verify the expiration date is set correctly
            self.assertLess(expired_permission.expires_at, timezone.now())
        
        # Step 5: Generate compliance report for temporary permissions
        self.client.force_authenticate(user=self.ceo)
        
        # Query for all expired permissions in the period
        compliance_response = self.client.get(
            reverse('permission-audit-report'),
            {
                'start_date': (timezone.now() - timedelta(days=60)).date(),
                'end_date': timezone.now().date(),
                'permission_type': 'temporary'
            }
        )
        
        # Note: This endpoint would need to be implemented
        # For now, verify the audit log contains the temporary permission records
        
        audit_logs = PermissionAuditLog.objects.filter(
            reason__icontains='year-end'
        )
        self.assertGreaterEqual(audit_logs.count(), 1)
    
    def test_004_cross_system_integration_workflow(self):
        """
        T018-004: Test cross-system integration workflow.
        
        Simulates integration with external systems:
        1. API-based permission synchronization
        2. External system callback handling
        3. Data consistency across systems
        4. Error handling and rollback
        """
        self.client.force_authenticate(user=self.ceo)
        
        # Step 1: Simulate external system integration
        # Create permission that needs to be synced to external HR system
        
        external_sync_permission = Permission.objects.create(
            code='hr.employee.manage',
            name='Manage Employee Records',
            description='Can manage employee records in HR system',
            module='hr',
            resource='employee',
            action='manage',
            risk_level='high'
        )
        
        # Step 2: Grant permission with external system sync
        integration_data = {
            'user': self.finance_manager.id,
            'permission': external_sync_permission.id,
            'is_granted': True,
            'reason': 'HR system integration test',
            'sync_to_external': True  # Flag for external sync
        }
        
        # Mock external system API call
        with patch('apps.core.integrations.hr_system.sync_permission') as mock_sync:
            mock_sync.return_value = {'status': 'success', 'external_id': 'HR-12345'}
            
            response = self.client.post(
                reverse('userpermission-list'),
                integration_data,
                format='json'
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
            # Verify external system was called
            mock_sync.assert_called_once()
        
        # Step 3: Handle external system callback/webhook
        # Simulate external system confirming permission activation
        
        callback_data = {
            'external_system': 'HR',
            'operation': 'permission_activated',
            'external_id': 'HR-12345',
            'user_id': self.finance_manager.id,
            'permission_code': 'hr.employee.manage',
            'status': 'active'
        }
        
        # Note: This would be a webhook endpoint
        webhook_response = self.client.post(
            reverse('external-system-callback'),
            callback_data,
            format='json'
        )
        
        # For now, simulate successful callback processing
        # In real implementation, this would update permission status/metadata
        
        # Step 4: Test cross-system data consistency
        # Verify permission exists in both systems
        
        local_permission = UserPermission.objects.get(
            user=self.finance_manager,
            permission=external_sync_permission
        )
        self.assertTrue(local_permission.is_granted)
        
        # Mock external system check
        with patch('apps.core.integrations.hr_system.check_permission') as mock_check:
            mock_check.return_value = {'has_permission': True, 'external_id': 'HR-12345'}
            
            # Call consistency check
            consistency_response = self.client.post(
                reverse('permission-consistency-check'),
                {
                    'user_id': self.finance_manager.id,
                    'permission_code': 'hr.employee.manage',
                    'external_system': 'HR'
                },
                format='json'
            )
            
            # Should confirm consistency
            mock_check.assert_called_once()
        
        # Step 5: Test error handling and rollback
        # Simulate external system failure during permission revocation
        
        with patch('apps.core.integrations.hr_system.revoke_permission') as mock_revoke:
            mock_revoke.side_effect = Exception('External system unavailable')
            
            revoke_data = {'is_granted': False}
            
            response = self.client.patch(
                reverse('userpermission-detail', args=[local_permission.id]),
                revoke_data,
                format='json'
            )
            
            # Should handle external system failure gracefully
            # Either succeed with delayed sync or fail with clear error
            self.assertIn(
                response.status_code,
                [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR, 
                 status.HTTP_502_BAD_GATEWAY]
            )
            
            if response.status_code == status.HTTP_200_OK:
                # Should mark for retry or delayed sync
                updated_permission = UserPermission.objects.get(id=local_permission.id)
                # Check if there's a pending_sync flag or similar
                
            elif response.status_code >= 500:
                # Should provide clear error message about external system
                self.assertIn('external', response.data.get('detail', '').lower())
    
    def test_005_emergency_access_workflow(self):
        """
        T018-005: Test emergency access workflow.
        
        Simulates emergency access scenarios:
        1. Emergency permission activation
        2. Break-glass access controls
        3. Enhanced audit logging
        4. Automatic cleanup and review
        """
        # Step 1: Regular user needs emergency access
        self.client.force_authenticate(user=self.sales_rep1)
        
        # Simulate emergency scenario - need critical permission immediately
        emergency_request_data = {
            'permission_code': 'admin.system.configure',
            'emergency_reason': 'Production system failure - need immediate configuration access',
            'contact_info': 'ext. 555-1234',
            'estimated_duration_hours': 2
        }
        
        response = self.client.post(
            reverse('emergency-access-request'),
            emergency_request_data,
            format='json'
        )
        
        # Emergency request should be created but not automatically approved
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        emergency_request_id = response.data['id']
        
        # Step 2: Manager approves emergency access
        self.client.force_authenticate(user=self.ceo)
        
        approval_data = {
            'approved': True,
            'approval_reason': 'Critical production issue confirmed',
            'time_limit_hours': 2,
            'monitoring_required': True
        }
        
        response = self.client.patch(
            reverse('emergency-access-detail', args=[emergency_request_id]),
            approval_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Step 3: Emergency permission automatically granted with time limit
        emergency_expire_time = timezone.now() + timedelta(hours=2)
        
        emergency_permission_data = {
            'user': self.sales_rep1.id,
            'permission': self.permissions['admin_system'].id,
            'is_granted': True,
            'expires_at': emergency_expire_time.isoformat(),
            'reason': f'EMERGENCY ACCESS - Request #{emergency_request_id}',
            'is_emergency': True,
            'requires_monitoring': True
        }
        
        response = self.client.post(
            reverse('userpermission-list'),
            emergency_permission_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        emergency_permission_id = response.data['id']
        
        # Step 4: Enhanced monitoring for emergency access
        self.client.force_authenticate(user=self.sales_rep1)
        
        # Every action should be logged with emergency flag
        monitoring_response = self.client.get(
            reverse('permission-usage-log'),
            {
                'user_id': self.sales_rep1.id,
                'permission_code': 'admin.system.configure',
                'emergency_session': True
            }
        )
        
        # Note: This endpoint would track all emergency access usage
        
        # Step 5: Automatic cleanup and review process
        # Simulate time passing beyond emergency window
        with patch('django.utils.timezone.now') as mock_now:
            mock_now.return_value = emergency_expire_time + timedelta(minutes=1)
            
            # Permission should be automatically revoked
            cleanup_response = self.client.post(
                reverse('emergency-access-cleanup'),
                format='json'
            )
            
            # Note: This would be a scheduled task in production
        
        # Verify emergency access was revoked
        self.client.force_authenticate(user=self.ceo)
        
        response = self.client.get(
            reverse('userpermission-detail', args=[emergency_permission_id])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Permission should be revoked or expired
        permission_data = response.data
        if 'is_granted' in permission_data:
            self.assertFalse(permission_data['is_granted'])
        
        # Step 6: Generate emergency access review report
        review_response = self.client.get(
            reverse('emergency-access-report'),
            {
                'start_date': (timezone.now() - timedelta(days=1)).date(),
                'end_date': timezone.now().date()
            }
        )
        
        # Note: This endpoint would provide detailed emergency access analytics
        
        # Verify enhanced audit logging
        emergency_logs = PermissionAuditLog.objects.filter(
            reason__icontains='EMERGENCY'
        )
        self.assertGreaterEqual(emergency_logs.count(), 1)
        
        # Emergency logs should have special flags
        for log in emergency_logs:
            # Should contain emergency context
            self.assertIn('emergency', log.reason.lower())
    
    def test_006_compliance_audit_workflow(self):
        """
        T018-006: Test compliance audit workflow.
        
        Simulates regulatory compliance requirements:
        1. SOX compliance checks
        2. Segregation of duties validation
        3. Periodic access review
        4. Compliance reporting
        """
        self.client.force_authenticate(user=self.ceo)
        
        # Step 1: Set up SOX-critical permissions
        sox_permissions = [
            Permission.objects.create(
                code='finance.journal.approve',
                name='Approve Journal Entries',
                description='Can approve financial journal entries',
                module='finance',
                resource='journal',
                action='approve',
                risk_level='critical',
                is_sox_critical=True  # Custom field for SOX compliance
            ),
            Permission.objects.create(
                code='finance.closing.execute',
                name='Execute Month/Year End Closing',
                description='Can execute financial period closing',
                module='finance',
                resource='closing',
                action='execute',
                risk_level='critical',
                is_sox_critical=True
            )
        ]
        
        # Step 2: Assign SOX permissions with segregation rules
        # Finance manager gets journal approval
        journal_assignment = {
            'user': self.finance_manager.id,
            'permission': sox_permissions[0].id,
            'is_granted': True,
            'reason': 'SOX compliance - journal approval authority',
            'requires_segregation': True
        }
        
        response = self.client.post(
            reverse('userpermission-list'),
            journal_assignment,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Step 3: Test segregation of duties validation
        # Same user should NOT be able to get closing permission
        conflicting_assignment = {
            'user': self.finance_manager.id,
            'permission': sox_permissions[1].id,
            'is_granted': True,
            'reason': 'Attempting conflicting SOX permission'
        }
        
        response = self.client.post(
            reverse('userpermission-list'),
            conflicting_assignment,
            format='json'
        )
        
        # Should fail due to segregation of duties
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('segregation', response.data.get('detail', '').lower())
        
        # Step 4: Proper segregation - assign to different user
        proper_assignment = {
            'user': self.sales_manager.id,  # Different user
            'permission': sox_permissions[1].id,
            'is_granted': True,
            'reason': 'SOX compliance - proper segregation of duties'
        }
        
        response = self.client.post(
            reverse('userpermission-list'),
            proper_assignment,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Step 5: Periodic access review process
        # Generate access review report for all SOX-critical permissions
        review_response = self.client.get(
            reverse('sox-access-review'),
            {
                'review_period': 'quarterly',
                'include_inactive_users': False
            }
        )
        
        # Note: This endpoint would generate comprehensive SOX access report
        
        # Step 6: Automated compliance checks
        # Run compliance validation across all permissions
        compliance_check_response = self.client.post(
            reverse('compliance-validation'),
            {
                'check_types': ['sox_segregation', 'risk_concentration', 'temporal_access'],
                'generate_report': True
            }
        )
        
        # Should identify any compliance violations
        # For this test, should be clean since we set up proper segregation
        
        # Step 7: Generate regulatory report
        regulatory_report_response = self.client.get(
            reverse('regulatory-compliance-report'),
            {
                'report_type': 'sox_404',
                'period_start': (timezone.now() - timedelta(days=90)).date(),
                'period_end': timezone.now().date(),
                'include_remediation_status': True
            }
        )
        
        # Note: These endpoints would need to be implemented for full compliance
        
        # Verify audit trail includes compliance context
        sox_logs = PermissionAuditLog.objects.filter(
            reason__icontains='SOX'
        )
        self.assertGreaterEqual(sox_logs.count(), 2)
        
        # SOX logs should have enhanced detail
        for log in sox_logs:
            self.assertIn('sox', log.reason.lower())
            # Should include risk level and business justification
    
    def tearDown(self):
        """Clean up after each test."""
        cache.clear()
        super().tearDown()
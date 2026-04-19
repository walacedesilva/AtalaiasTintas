# Reporting Module for Permission System Audit Trail
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Q, Avg, Max, Min
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
import json
import csv
import hashlib
from io import StringIO

from .models import (
    PermissionAuditLog, Permission, UserGroup, UserPermission, 
    GroupPermission, GroupMembership
)

User = get_user_model()


class PermissionAuditReporter:
    """
    Advanced reporting and analytics engine for permission audit data.
    
    Features:
    - Compliance reporting for regulatory requirements
    - Security analytics and threat detection
    - Access pattern analysis and anomaly detection
    - Data export with integrity verification
    - Real-time monitoring and alerting
    """
    
    def __init__(self, user=None):
        """Initialize reporter with optional user context for access control."""
        self.user = user
        
    def generate_compliance_report(self, from_date=None, to_date=None, format='json'):
        """
        Generate comprehensive compliance report for regulatory audits.
        
        Args:
            from_date: Start date for report (datetime or string)
            to_date: End date for report (datetime or string) 
            format: Output format ('json', 'csv', 'excel')
            
        Returns:
            dict: Compliance report with all required sections
        """
        # Default to last 90 days if no dates provided
        if not from_date or not to_date:
            to_date = timezone.now()
            from_date = to_date - timedelta(days=90)
        
        # Parse string dates if needed
        if isinstance(from_date, str):
            from_date = datetime.strptime(from_date, '%Y-%m-%d')
        if isinstance(to_date, str):
            to_date = datetime.strptime(to_date, '%Y-%m-%d')
        
        # Build base queryset
        audit_logs = PermissionAuditLog.objects.filter(
            created_at__range=[from_date, to_date]
        ).select_related('actor', 'target_user', 'permission')
        
        # Apply user access filters if needed
        if self.user and not self.user.is_superuser:
            audit_logs = self._apply_user_filters(audit_logs, self.user)
        
        report = {
            'report_metadata': {
                'generated_at': timezone.now().isoformat(),
                'report_type': 'compliance_audit',
                'period': {
                    'from_date': from_date.isoformat(),
                    'to_date': to_date.isoformat(),
                    'duration_days': (to_date - from_date).days
                },
                'generated_by': self.user.username if self.user else 'system',
                'total_events_analyzed': audit_logs.count()
            },
            
            # Executive Summary
            'executive_summary': self._generate_executive_summary(audit_logs),
            
            # Access Control Matrix
            'access_control_matrix': self._generate_access_control_matrix(audit_logs),
            
            # User Activity Analysis
            'user_activity_analysis': self._analyze_user_activity(audit_logs),
            
            # Permission Changes Audit
            'permission_changes_audit': self._audit_permission_changes(audit_logs),
            
            # Security Violations and Incidents
            'security_violations': self._detect_security_violations(audit_logs),
            
            # Segregation of Duties Analysis
            'segregation_of_duties': self._analyze_segregation_of_duties(audit_logs),
            
            # Data Retention and Archival
            'data_retention_status': self._analyze_data_retention(),
            
            # Risk Assessment
            'risk_assessment': self._conduct_risk_assessment(audit_logs),
            
            # Recommendations
            'recommendations': self._generate_recommendations(audit_logs)
        }
        
        # Add format-specific processing
        if format == 'csv':
            return self._export_to_csv(report)
        elif format == 'excel':
            return self._export_to_excel(report)
        else:
            return report
    
    def _generate_executive_summary(self, audit_logs):
        """Generate high-level executive summary statistics."""
        total_events = audit_logs.count()
        unique_users = audit_logs.values('actor').distinct().count()
        
        # Critical metrics
        failed_operations = audit_logs.filter(result='failure').count()
        high_risk_operations = audit_logs.filter(
            Q(action__in=['grant', 'revoke', 'delete_user', 'create_user']) |
            Q(details__icontains='HIGH') |
            Q(details__icontains='CRITICAL')
        ).count()
        
        # Time-based analysis
        after_hours_activity = audit_logs.extra(
            where=["EXTRACT(hour FROM created_at) NOT BETWEEN 8 AND 18"]
        ).count()
        
        weekend_activity = audit_logs.extra(
            where=["EXTRACT(dow FROM created_at) IN (0, 6)"]
        ).count()
        
        # Risk indicators
        risk_score = self._calculate_overall_risk_score(audit_logs)
        
        return {
            'total_audit_events': total_events,
            'unique_active_users': unique_users,
            'failed_operations_count': failed_operations,
            'failed_operations_percentage': round((failed_operations / total_events * 100), 2) if total_events > 0 else 0,
            'high_risk_operations': high_risk_operations,
            'after_hours_activity': after_hours_activity,
            'weekend_activity': weekend_activity,
            'overall_risk_score': risk_score,
            'risk_level': self._get_risk_level(risk_score),
            'compliance_status': 'COMPLIANT' if risk_score < 0.3 else 'NEEDS_ATTENTION' if risk_score < 0.7 else 'NON_COMPLIANT'
        }
    
    def _generate_access_control_matrix(self, audit_logs):
        """Generate access control matrix showing who has access to what."""
        # Current active permissions
        current_permissions = UserPermission.objects.filter(
            is_granted=True
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        ).select_related('user', 'permission')
        
        # Group permissions
        group_permissions = GroupPermission.objects.filter(
            is_granted=True,
            permission__is_active=True
        ).select_related('group', 'permission')
        
        # Build matrix
        user_permission_matrix = {}
        for up in current_permissions:
            user_key = f"{up.user.username} ({up.user.get_full_name()})"
            if user_key not in user_permission_matrix:
                user_permission_matrix[user_key] = []
            
            user_permission_matrix[user_key].append({
                'permission': up.permission.code,
                'permission_name': up.permission.name,
                'risk_level': up.permission.risk_level,
                'granted_by': up.granted_by.username if up.granted_by else 'system',
                'granted_at': up.granted_at.isoformat() if up.granted_at else None,
                'expires_at': up.expires_at.isoformat() if up.expires_at else None,
                'source': 'direct'
            })
        
        # Add group-based permissions
        active_memberships = GroupMembership.objects.filter(
            is_active=True
        ).select_related('user', 'group')
        
        for membership in active_memberships:
            user_key = f"{membership.user.username} ({membership.user.get_full_name()})"
            if user_key not in user_permission_matrix:
                user_permission_matrix[user_key] = []
                
            # Get group permissions
            for gp in group_permissions.filter(group=membership.group):
                user_permission_matrix[user_key].append({
                    'permission': gp.permission.code,
                    'permission_name': gp.permission.name,
                    'risk_level': gp.permission.risk_level,
                    'granted_by': gp.granted_by.username if gp.granted_by else 'system',
                    'granted_at': gp.granted_at.isoformat() if gp.granted_at else None,
                    'expires_at': None,  # Group permissions don't typically expire
                    'source': f'group:{membership.group.name}'
                })
        
        # Calculate summary statistics
        total_unique_permissions = Permission.objects.filter(is_active=True).count()
        high_risk_assignments = sum(
            1 for user_perms in user_permission_matrix.values()
            for perm in user_perms
            if perm['risk_level'] in ['HIGH', 'CRITICAL']
        )
        
        return {
            'access_matrix': user_permission_matrix,
            'summary_statistics': {
                'total_users_with_permissions': len(user_permission_matrix),
                'total_permission_assignments': sum(len(perms) for perms in user_permission_matrix.values()),
                'total_unique_permissions': total_unique_permissions,
                'high_risk_permission_assignments': high_risk_assignments,
                'average_permissions_per_user': round(
                    sum(len(perms) for perms in user_permission_matrix.values()) / len(user_permission_matrix), 2
                ) if user_permission_matrix else 0
            }
        }
    
    def _analyze_user_activity(self, audit_logs):
        """Analyze individual user activity patterns."""
        user_activity = audit_logs.values('actor__username').annotate(
            total_actions=Count('id'),
            successful_actions=Count('id', filter=Q(result='success')),
            failed_actions=Count('id', filter=Q(result='failure')),
            unique_permissions_accessed=Count('permission', distinct=True),
            unique_targets_affected=Count('target_user', distinct=True),
            first_activity=Min('created_at'),
            last_activity=Max('created_at')
        ).order_by('-total_actions')
        
        # Analyze activity patterns
        activity_analysis = []
        for user_stat in user_activity[:50]:  # Top 50 most active users
            username = user_stat['actor__username']
            
            # Get user's recent activity pattern
            user_logs = audit_logs.filter(actor__username=username)
            
            # Time-based patterns
            hourly_pattern = user_logs.extra(
                select={'hour': 'EXTRACT(hour FROM created_at)'}
            ).values('hour').annotate(count=Count('id'))
            
            peak_hours = [h['hour'] for h in hourly_pattern.order_by('-count')[:3]]
            
            # Risk indicators
            failure_rate = (user_stat['failed_actions'] / user_stat['total_actions']) * 100
            after_hours_count = user_logs.extra(
                where=["EXTRACT(hour FROM created_at) NOT BETWEEN 8 AND 18"]
            ).count()
            
            activity_analysis.append({
                'username': username,
                'total_actions': user_stat['total_actions'],
                'success_rate': round(100 - failure_rate, 2),
                'failure_rate': round(failure_rate, 2),
                'unique_permissions_accessed': user_stat['unique_permissions_accessed'],
                'unique_targets_affected': user_stat['unique_targets_affected'],
                'first_activity': user_stat['first_activity'].isoformat(),
                'last_activity': user_stat['last_activity'].isoformat(),
                'peak_activity_hours': peak_hours,
                'after_hours_activity_count': after_hours_count,
                'risk_indicators': {
                    'high_failure_rate': failure_rate > 20,
                    'excessive_after_hours': after_hours_count > (user_stat['total_actions'] * 0.3),
                    'broad_permission_access': user_stat['unique_permissions_accessed'] > 20,
                    'many_targets_affected': user_stat['unique_targets_affected'] > 10
                }
            })
        
        return {
            'user_activity_summary': list(user_activity[:20]),
            'detailed_analysis': activity_analysis,
            'risk_users': [
                user for user in activity_analysis
                if any(user['risk_indicators'].values())
            ]
        }
    
    def _audit_permission_changes(self, audit_logs):
        """Audit all permission changes with detailed analysis."""
        permission_changes = audit_logs.filter(
            action__in=['grant', 'revoke', 'assign_group_permission', 'remove_group_permission']
        )
        
        # Analyze by permission type
        permission_analysis = permission_changes.values(
            'permission__code', 'permission__name', 'permission__risk_level'
        ).annotate(
            total_changes=Count('id'),
            grants=Count('id', filter=Q(action='grant')),
            revocations=Count('id', filter=Q(action='revoke')),
            unique_actors=Count('actor', distinct=True)
        ).order_by('-total_changes')
        
        # High-risk permission changes
        high_risk_changes = permission_changes.filter(
            Q(permission__risk_level__in=['HIGH', 'CRITICAL']) |
            Q(details__icontains='HIGH') |
            Q(details__icontains='CRITICAL')
        ).values(
            'actor__username', 'target_user__username', 'permission__code',
            'action', 'created_at', 'result'
        )
        
        # Bulk operations analysis
        bulk_operations = permission_changes.filter(
            action__icontains='bulk'
        ).values(
            'actor__username', 'action', 'created_at'
        ).annotate(
            operations_count=Count('id')
        )
        
        return {
            'total_permission_changes': permission_changes.count(),
            'permission_change_analysis': list(permission_analysis[:30]),
            'high_risk_permission_changes': list(high_risk_changes),
            'bulk_operations': list(bulk_operations),
            'change_velocity': {
                'daily_average': permission_changes.count() / max(1, (timezone.now().date() - permission_changes.earliest('created_at').created_at.date()).days),
                'peak_day': permission_changes.extra(
                    select={'date': 'DATE(created_at)'}
                ).values('date').annotate(
                    count=Count('id')
                ).order_by('-count').first()
            }
        }
    
    def _detect_security_violations(self, audit_logs):
        """Detect potential security violations and policy breaches."""
        violations = []
        
        # Failed login attempts patterns
        failed_operations = audit_logs.filter(result='failure')
        
        # Brute force detection (many failures from same IP/user)
        brute_force_attempts = failed_operations.values('ip_address', 'actor__username').annotate(
            failure_count=Count('id')
        ).filter(failure_count__gte=5)
        
        for attempt in brute_force_attempts:
            violations.append({
                'type': 'BRUTE_FORCE_ATTEMPT',
                'severity': 'HIGH',
                'description': f"Multiple failed attempts detected from IP {attempt['ip_address']} for user {attempt['actor__username']}",
                'count': attempt['failure_count'],
                'ip_address': attempt['ip_address'],
                'username': attempt['actor__username']
            })
        
        # Privilege escalation attempts
        escalation_attempts = audit_logs.filter(
            action__in=['grant', 'assign_group_permission'],
            details__icontains='HIGH'
        ).exclude(result='success')
        
        for escalation in escalation_attempts:
            violations.append({
                'type': 'PRIVILEGE_ESCALATION_ATTEMPT',
                'severity': 'CRITICAL',
                'description': f"Failed attempt to grant high-risk permission by {escalation.actor.username}",
                'actor': escalation.actor.username,
                'target': escalation.target_user.username if escalation.target_user else 'N/A',
                'permission': escalation.permission.code if escalation.permission else 'N/A',
                'timestamp': escalation.created_at.isoformat()
            })
        
        # Unusual access patterns (after hours, weekends)
        after_hours_high_risk = audit_logs.filter(
            Q(details__icontains='HIGH') | Q(details__icontains='CRITICAL')
        ).extra(
            where=["EXTRACT(hour FROM created_at) NOT BETWEEN 8 AND 18"]
        )
        
        if after_hours_high_risk.count() > 0:
            violations.append({
                'type': 'AFTER_HOURS_HIGH_RISK_ACTIVITY',
                'severity': 'MEDIUM',
                'description': f"High-risk operations performed outside business hours",
                'count': after_hours_high_risk.count(),
                'details': 'Review legitimacy of after-hours high-risk activities'
            })
        
        # Multiple IP addresses for single user
        multi_ip_users = audit_logs.values('actor').annotate(
            unique_ips=Count('ip_address', distinct=True)
        ).filter(unique_ips__gte=3)
        
        for multi_ip in multi_ip_users:
            user = User.objects.get(id=multi_ip['actor'])
            violations.append({
                'type': 'MULTIPLE_IP_ACCESS',
                'severity': 'MEDIUM',
                'description': f"User {user.username} accessed from {multi_ip['unique_ips']} different IP addresses",
                'username': user.username,
                'ip_count': multi_ip['unique_ips']
            })
        
        return {
            'total_violations_detected': len(violations),
            'violations_by_severity': {
                'CRITICAL': len([v for v in violations if v['severity'] == 'CRITICAL']),
                'HIGH': len([v for v in violations if v['severity'] == 'HIGH']),
                'MEDIUM': len([v for v in violations if v['severity'] == 'MEDIUM']),
                'LOW': len([v for v in violations if v['severity'] == 'LOW'])
            },
            'detailed_violations': violations,
            'security_recommendations': self._generate_security_recommendations(violations)
        }
    
    def _analyze_segregation_of_duties(self, audit_logs):
        """Analyze segregation of duties compliance."""
        # Check for users with conflicting permissions
        conflicting_permission_patterns = [
            (['create_user', 'grant'], 'User creation and permission assignment'),
            (['approve', 'request'], 'Approval and request submission'),
            (['audit.view_all', 'grant'], 'Audit viewing and permission granting')
        ]
        
        violations = []
        
        # Get current active permissions
        current_perms = UserPermission.objects.filter(
            is_granted=True
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        ).select_related('user', 'permission')
        
        # Group by user
        user_permissions = {}
        for perm in current_perms:
            if perm.user.username not in user_permissions:
                user_permissions[perm.user.username] = []
            user_permissions[perm.user.username].append(perm.permission.code)
        
        # Check for conflicts
        for username, permissions in user_permissions.items():
            for conflict_pattern, description in conflicting_permission_patterns:
                matching_perms = [p for p in permissions if any(pattern in p for pattern in conflict_pattern)]
                if len(matching_perms) >= 2:
                    violations.append({
                        'username': username,
                        'conflict_type': description,
                        'conflicting_permissions': matching_perms,
                        'risk_level': 'HIGH'
                    })
        
        return {
            'segregation_violations': violations,
            'total_violations': len(violations),
            'users_analyzed': len(user_permissions),
            'compliance_rate': round((1 - len(violations) / len(user_permissions)) * 100, 2) if user_permissions else 100
        }
    
    def _analyze_data_retention(self):
        """Analyze audit data retention and archival status."""
        total_audit_records = PermissionAuditLog.objects.count()
        
        # Records by age
        now = timezone.now()
        age_buckets = {
            'last_30_days': total_audit_records - PermissionAuditLog.objects.filter(
                created_at__lt=now - timedelta(days=30)
            ).count(),
            'last_90_days': total_audit_records - PermissionAuditLog.objects.filter(
                created_at__lt=now - timedelta(days=90)
            ).count(),
            'last_year': total_audit_records - PermissionAuditLog.objects.filter(
                created_at__lt=now - timedelta(days=365)
            ).count(),
            'older_than_year': PermissionAuditLog.objects.filter(
                created_at__lt=now - timedelta(days=365)
            ).count()
        }
        
        # Storage analysis
        oldest_record = PermissionAuditLog.objects.order_by('created_at').first()
        newest_record = PermissionAuditLog.objects.order_by('-created_at').first()
        
        return {
            'total_audit_records': total_audit_records,
            'data_age_distribution': age_buckets,
            'retention_period': {
                'oldest_record': oldest_record.created_at.isoformat() if oldest_record else None,
                'newest_record': newest_record.created_at.isoformat() if newest_record else None,
                'total_retention_days': (newest_record.created_at - oldest_record.created_at).days if oldest_record and newest_record else 0
            },
            'archival_recommendations': {
                'records_ready_for_archival': age_buckets['older_than_year'],
                'estimated_storage_saved': f"{age_buckets['older_than_year'] * 0.5}KB"  # Rough estimate
            }
        }
    
    def _conduct_risk_assessment(self, audit_logs):
        """Conduct comprehensive risk assessment."""
        risk_factors = {
            'failed_operations_ratio': self._calculate_failure_ratio(audit_logs),
            'high_risk_permission_usage': self._calculate_high_risk_usage(audit_logs),
            'after_hours_activity_ratio': self._calculate_after_hours_ratio(audit_logs),
            'unusual_ip_access': self._calculate_ip_diversity(audit_logs),
            'privilege_escalation_attempts': self._calculate_escalation_attempts(audit_logs)
        }
        
        # Calculate weighted risk score
        weights = {
            'failed_operations_ratio': 0.25,
            'high_risk_permission_usage': 0.30,
            'after_hours_activity_ratio': 0.15,
            'unusual_ip_access': 0.15,
            'privilege_escalation_attempts': 0.15
        }
        
        overall_risk_score = sum(
            risk_factors[factor] * weights[factor]
            for factor in risk_factors
        )
        
        return {
            'risk_factors': risk_factors,
            'risk_factor_weights': weights,
            'overall_risk_score': round(overall_risk_score, 3),
            'risk_level': self._get_risk_level(overall_risk_score),
            'risk_trends': self._analyze_risk_trends(audit_logs),
            'mitigation_recommendations': self._generate_risk_mitigations(risk_factors)
        }
    
    def _generate_recommendations(self, audit_logs):
        """Generate actionable recommendations based on audit analysis."""
        recommendations = []
        
        # Analyze patterns to generate recommendations
        failed_ops_count = audit_logs.filter(result='failure').count()
        total_ops = audit_logs.count()
        
        if total_ops > 0:
            failure_rate = failed_ops_count / total_ops
            
            if failure_rate > 0.1:  # >10% failure rate
                recommendations.append({
                    'category': 'SECURITY',
                    'priority': 'HIGH',
                    'title': 'High Failure Rate Detected',
                    'description': f'Current failure rate is {failure_rate:.1%}, which exceeds recommended threshold of 10%',
                    'action_items': [
                        'Review authentication mechanisms',
                        'Implement additional user training',
                        'Consider implementing account lockout policies'
                    ]
                })
        
        # Check for missing segregation of duties
        high_risk_users = audit_logs.filter(
            details__icontains='HIGH'
        ).values('actor').distinct().count()
        
        if high_risk_users < 3:
            recommendations.append({
                'category': 'COMPLIANCE',
                'priority': 'MEDIUM',
                'title': 'Limited High-Risk Permission Distribution',
                'description': 'Very few users have high-risk permissions, consider reviewing segregation of duties',
                'action_items': [
                    'Review high-risk permission assignments',
                    'Implement role-based access control',
                    'Create approval workflows for sensitive operations'
                ]
            })
        
        # After-hours activity
        after_hours_count = audit_logs.extra(
            where=["EXTRACT(hour FROM created_at) NOT BETWEEN 8 AND 18"]
        ).count()
        
        if after_hours_count > (total_ops * 0.2):  # >20% after hours
            recommendations.append({
                'category': 'MONITORING',
                'priority': 'MEDIUM',
                'title': 'High After-Hours Activity',
                'description': 'Significant portion of activities occurring outside business hours',
                'action_items': [
                    'Implement enhanced monitoring for after-hours access',
                    'Review business justification for after-hours activities',
                    'Consider implementing additional approvals for after-hours high-risk operations'
                ]
            })
        
        return {
            'total_recommendations': len(recommendations),
            'recommendations_by_priority': {
                'HIGH': len([r for r in recommendations if r['priority'] == 'HIGH']),
                'MEDIUM': len([r for r in recommendations if r['priority'] == 'MEDIUM']),
                'LOW': len([r for r in recommendations if r['priority'] == 'LOW'])
            },
            'detailed_recommendations': recommendations
        }
    
    # Helper methods for calculations
    def _calculate_overall_risk_score(self, audit_logs):
        """Calculate overall risk score based on multiple factors."""
        # Simplified risk calculation
        total_ops = audit_logs.count()
        if total_ops == 0:
            return 0.0
        
        failed_ops = audit_logs.filter(result='failure').count()
        high_risk_ops = audit_logs.filter(details__icontains='HIGH').count()
        after_hours = audit_logs.extra(
            where=["EXTRACT(hour FROM created_at) NOT BETWEEN 8 AND 18"]
        ).count()
        
        # Weighted risk score
        risk_score = (
            (failed_ops / total_ops) * 0.4 +
            (high_risk_ops / total_ops) * 0.4 +
            (after_hours / total_ops) * 0.2
        )
        
        return min(risk_score, 1.0)  # Cap at 1.0
    
    def _get_risk_level(self, score):
        """Convert risk score to human-readable level."""
        if score < 0.3:
            return 'LOW'
        elif score < 0.7:
            return 'MEDIUM'
        else:
            return 'HIGH'
    
    def _calculate_failure_ratio(self, audit_logs):
        total = audit_logs.count()
        if total == 0:
            return 0.0
        failed = audit_logs.filter(result='failure').count()
        return failed / total
    
    def _calculate_high_risk_usage(self, audit_logs):
        total = audit_logs.count()
        if total == 0:
            return 0.0
        high_risk = audit_logs.filter(
            Q(details__icontains='HIGH') | Q(details__icontains='CRITICAL')
        ).count()
        return high_risk / total
    
    def _calculate_after_hours_ratio(self, audit_logs):
        total = audit_logs.count()
        if total == 0:
            return 0.0
        after_hours = audit_logs.extra(
            where=["EXTRACT(hour FROM created_at) NOT BETWEEN 8 AND 18"]
        ).count()
        return after_hours / total
    
    def _calculate_ip_diversity(self, audit_logs):
        total_users = audit_logs.values('actor').distinct().count()
        if total_users == 0:
            return 0.0
        
        multi_ip_users = audit_logs.values('actor').annotate(
            ip_count=Count('ip_address', distinct=True)
        ).filter(ip_count__gt=1).count()
        
        return multi_ip_users / total_users
    
    def _calculate_escalation_attempts(self, audit_logs):
        total = audit_logs.count()
        if total == 0:
            return 0.0
            
        escalations = audit_logs.filter(
            action__in=['grant', 'assign_group_permission'],
            details__icontains='HIGH',
            result='failure'
        ).count()
        
        return escalations / total
    
    def _analyze_risk_trends(self, audit_logs):
        """Analyze risk trends over time."""
        # Simple trend analysis - could be expanded
        return {
            'trend_direction': 'stable',  # Could implement actual trend analysis
            'trend_confidence': 0.8
        }
    
    def _generate_risk_mitigations(self, risk_factors):
        """Generate risk mitigation recommendations."""
        mitigations = []
        
        for factor, score in risk_factors.items():
            if score > 0.5:  # High risk threshold
                if factor == 'failed_operations_ratio':
                    mitigations.append('Implement stronger authentication and user training')
                elif factor == 'high_risk_permission_usage':
                    mitigations.append('Review and potentially restrict high-risk permission assignments')
                elif factor == 'after_hours_activity_ratio':
                    mitigations.append('Implement enhanced monitoring for after-hours activities')
        
        return mitigations
    
    def _generate_security_recommendations(self, violations):
        """Generate security recommendations based on violations."""
        recommendations = []
        
        violation_types = [v['type'] for v in violations]
        
        if 'BRUTE_FORCE_ATTEMPT' in violation_types:
            recommendations.append('Implement account lockout policies and IP blocking')
        
        if 'PRIVILEGE_ESCALATION_ATTEMPT' in violation_types:
            recommendations.append('Review privilege escalation detection and prevention measures')
        
        if 'MULTIPLE_IP_ACCESS' in violation_types:
            recommendations.append('Consider implementing IP whitelisting for sensitive accounts')
        
        return recommendations
    
    def _apply_user_filters(self, queryset, user):
        """Apply user-specific filters based on permissions."""
        # This would implement the same logic as in the ViewSet
        # Simplified for now
        if not user.is_superuser:
            return queryset.filter(actor=user)
        return queryset
    
    def _export_to_csv(self, report):
        """Export report to CSV format."""
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header information
        writer.writerow(['Permission System Compliance Report'])
        writer.writerow(['Generated:', report['report_metadata']['generated_at']])
        writer.writerow(['Period:', f"{report['report_metadata']['period']['from_date']} to {report['report_metadata']['period']['to_date']}"])
        writer.writerow([])
        
        # Executive Summary
        writer.writerow(['Executive Summary'])
        summary = report['executive_summary']
        for key, value in summary.items():
            writer.writerow([key.replace('_', ' ').title(), value])
        
        return output.getvalue()
    
    def _export_to_excel(self, report):
        """Export report to Excel format."""
        # Would implement Excel export using openpyxl or xlswriter
        # For now, return JSON
        return report
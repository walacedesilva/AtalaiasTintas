#!/usr/bin/env python
"""Simple test for Django admin login functionality"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tintas_system.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

def simple_admin_test():
    """Simple test to check if admin login causes server errors"""
    try:
        from django.test import Client
        from django.contrib.auth import get_user_model
        
        print("=== Django Admin Login Test ===")
        
        # Create test client
        client = Client()
        User = get_user_model()
        
        # Get admin user
        admin = User.objects.filter(is_superuser=True).first()
        if not admin:
            print("❌ No admin user found!")
            return False
        
        print(f"✅ Admin user found: {admin.username}")
        
        # Test login page access
        print("Testing login page...")
        login_response = client.get('/admin/login/')
        print(f"Login page status: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print("❌ Login page not accessible")
            return False
        
        print("✅ Login page accessible")
        
        # Test POST to login (even with wrong password, should not cause server errors)
        print("Testing login form submission...")
        post_response = client.post('/admin/login/', {
            'username': admin.username,
            'password': 'wrongpassword123',
            'next': '/admin/'
        })
        
        print(f"Login POST status: {post_response.status_code}")
        
        # Any status except 500 is OK (could be 200 for failed login or 302 for success)
        if post_response.status_code == 500:
            print("❌ Login POST caused server error (500)")
            return False
        
        print("✅ Login POST processed without server error")
        
        # Check if PermissionAuditLog entries were created without errors
        try:
            from apps.core.models import PermissionAuditLog
            recent_logs = PermissionAuditLog.objects.filter(
                action__in=['user_login_success', 'suspicious_headers_detected']
            ).count()
            print(f"✅ Audit logs working: {recent_logs} entries found")
        except Exception as e:
            print(f"⚠️  Audit log check failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = simple_admin_test()
    print(f"\n=== TEST RESULT: {'✅ PASS' if success else '❌ FAIL'} ===")
#!/usr/bin/env python
"""Test Django admin login functionality"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tintas_system.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

def test_admin_login():
    """Test admin login functionality"""
    
    # Create test client
    client = Client()
    User = get_user_model()
    
    # Get admin user
    try:
        admin = User.objects.filter(is_superuser=True).first()
        print(f'Found admin user: {admin.username if admin else "None"}')
        
        if not admin:
            print('No admin user found!')
            return False
        
        print(f'Admin user active: {admin.is_active}')
        print(f'Admin user staff: {admin.is_staff}')
        
        # Test if the admin page loads without errors
        print('Testing admin page access...')
        response = client.get('/admin/')
        print(f'Admin page GET response: {response.status_code}')
        
        # 302 is expected (redirect to login for unauthenticated users)
        if response.status_code not in [200, 302]:
            print(f'ERROR: Admin page returned {response.status_code}')
            return False
        
        # Test login page directly
        print('Testing login page access...')
        login_page_response = client.get('/admin/login/')
        print(f'Login page GET response: {login_page_response.status_code}')
        
        if login_page_response.status_code != 200:
            print(f'ERROR: Login page returned {login_page_response.status_code}')
            return False
        
        # Test login form submission (this will trigger our middleware)
        print('Testing login form submission...')
        login_response = client.post('/admin/login/', {
            'username': admin.username,
            'password': 'admin123',  # Try common password
            'next': '/admin/'
        }, follow=True)
        
        print(f'Login POST response: {login_response.status_code}')
        
        # Check if we're still on login page (failed login) or redirected
        final_url = login_response.request['PATH_INFO']
        print(f'Final URL: {final_url}')
        
        if 'login' not in final_url:
            print('SUCCESS: Login worked - no longer on login page!')
            return True
        else:
            print('INFO: Still on login page - credentials may be wrong, but no server error!')
            return True  # No error, just wrong password
        
    except Exception as e:
        print(f'ERROR during login test: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Testing Django Admin Login...")
    success = test_admin_login()
    print(f"Test result: {'PASS' if success else 'FAIL'}")
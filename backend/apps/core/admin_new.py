"""
Django admin configuration for core app models.

Feature: 3-modern-web-interface
Task: T006 - User Preferences Model
"""

from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserPreferences


@admin.register(UserPreferences)
class UserPreferencesAdmin(admin.ModelAdmin):
    """
    Admin interface for UserPreferences model.
    Provides comprehensive management of user interface preferences.
    """
    
    list_display = [
        'user', 
        'theme', 
        'density', 
        'sidebar_collapsed',
        'show_breadcrumbs',
        'high_contrast',
        'updated_at'
    ]
    
    list_filter = [
        'theme',
        'density', 
        'sidebar_collapsed',
        'show_breadcrumbs',
        'high_contrast',
        'reduce_motion',
        'created_at',
        'updated_at'
    ]
    
    search_fields = [
        'user__username',
        'user__first_name', 
        'user__last_name',
        'user__email'
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',),
            'description': 'User account associated with these preferences'
        }),
        ('Visual Preferences', {
            'fields': ('theme', 'density', 'high_contrast'),
            'description': 'Appearance and visual settings'
        }),
        ('Layout Preferences', {
            'fields': ('sidebar_collapsed', 'show_breadcrumbs'),
            'description': 'Navigation and layout configuration'
        }),
        ('Accessibility', {
            'fields': ('reduce_motion',),
            'description': 'Accessibility and motion preferences'
        }),
        ('Quick Actions', {
            'fields': ('quick_actions',),
            'description': 'JSON configuration for quick action buttons',
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'description': 'Creation and modification dates',
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-updated_at']
    
    def has_delete_permission(self, request, obj=None):
        """
        Prevent deletion of UserPreferences to maintain data integrity.
        Users should only be able to modify, not delete preferences.
        """
        return False
    
    def get_queryset(self, request):
        """Optimize queries by selecting related user data"""
        return super().get_queryset(request).select_related('user')


# Inline admin for UserPreferences within User admin
class UserPreferencesInline(admin.StackedInline):
    """
    Inline admin to show UserPreferences directly in the User admin page.
    """
    model = UserPreferences
    can_delete = False
    verbose_name = "Interface Preferences"
    verbose_name_plural = "Interface Preferences"
    
    fieldsets = (
        ('Visual Theme', {
            'fields': ('theme', 'density', 'high_contrast'),
            'classes': ('wide',)
        }),
        ('Layout', {
            'fields': ('sidebar_collapsed', 'show_breadcrumbs', 'reduce_motion'),
            'classes': ('wide',)
        }),
        ('Quick Actions', {
            'fields': ('quick_actions',),
            'classes': ('collapse', 'wide'),
            'description': 'JSON configuration for personalized quick actions'
        }),
    )


# Extend the default User admin to include preferences
class UserAdmin(BaseUserAdmin):
    """
    Enhanced User admin with UserPreferences inline.
    """
    inlines = [UserPreferencesInline]


# Unregister the default User admin and register our enhanced version
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
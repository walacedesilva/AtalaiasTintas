"""
Signal handlers for the core app.

Feature: 3-modern-web-interface
Task: T006 - User Preferences Model
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserPreferences

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_preferences(sender, instance, created, **kwargs):
    """
    Automatically create UserPreferences when a new User is created.
    
    This ensures every user has associated interface preferences with
    sensible defaults from the moment their account is created.
    
    Args:
        sender: The User model class
        instance: The specific User instance that was saved
        created: Boolean indicating if this is a new user
        **kwargs: Additional signal arguments
    """
    if created:
        UserPreferences.objects.create(
            user=instance,
            theme='light',
            density='comfortable',
            sidebar_collapsed=False,
            show_breadcrumbs=True,
            high_contrast=False,
            reduce_motion=False,
            quick_actions=[
                {'action': 'create_label', 'label': 'Nova Etiqueta', 'icon': 'bi-tag'},
                {'action': 'inventory_count', 'label': 'Contagem', 'icon': 'bi-clipboard-check'},
                {'action': 'sales_report', 'label': 'Vendas', 'icon': 'bi-graph-up'},
                {'action': 'tint_mix', 'label': 'Misturar Tinta', 'icon': 'bi-palette'},
            ]
        )
"""
Django settings package initialization.
Loads environment-specific settings based on DJANGO_SETTINGS_MODULE.
"""

import os
from decouple import config

# Get environment from DJANGO_ENVIRONMENT or default to development
ENVIRONMENT = config('DJANGO_ENVIRONMENT', default='development')

# Import appropriate settings module
if ENVIRONMENT == 'production':
    from .production import *
elif ENVIRONMENT == 'testing':
    from .testing import *
else:
    from .development import *
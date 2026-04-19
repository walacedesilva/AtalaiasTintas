"""
Settings básicas para desenvolvimento - versão simplificada
Usado para executar o projeto sem as funcionalidades mais complexas
"""

from .settings import *

# Apps do projeto - agora com core reabilitado
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party basics
    'rest_framework',
    'corsheaders',
    
    # Apps básicas do projeto 
    'apps.core',  # Reabilitado após correção dos syntax errors
    'apps.companies',  # Reabilitado - gestão de empresas e lojas
    'apps.inventory',  # Reabilitado - gestão de estoque 
    'apps.sales',  # Reabilitado - vendas e PDV
    'apps.fiscal',  # Reabilitado - NFe e conformidade fiscal
    'apps.tintometry',  # Reabilitado - sistema tintométrico
    'apps.marketplaces',  # Reabilitado - integração marketplaces
    'apps.monitoring',  # Reabilitado - monitoramento e logs
    # 'apps.inventory',
    # 'apps.sales',
    # 'apps.fiscal',
    # 'apps.marketplaces',
    # 'apps.companies',
    # 'apps.monitoring',
]

# Middleware básico
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware', 
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# URLs básicas
ROOT_URLCONF = 'tintas_system.urls_simple'

# Debug sempre True para desenvolvimento
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'localhost:8000']

# Database SQLite simples
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_simple.sqlite3',
    }
}

# Cache simples
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Configuração de logging simplificada para reduzir verbosity
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'WARNING',  # Apenas warnings e erros
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.utils.autoreload': {
            'handlers': [],
            'level': 'CRITICAL',  # Silenciar autoreload logs
            'propagate': False,
        },
    },
}
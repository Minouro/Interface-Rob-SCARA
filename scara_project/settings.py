# scara_project/settings.py

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-dummy-key-for-development-final'
DEBUG = True

# Lê os hosts permitidos de uma variável de ambiente que nosso script 'run.py' irá criar.
ALLOWED_HOSTS_STR = os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost')
ALLOWED_HOSTS = ALLOWED_HOSTS_STR.split(',')

# 'daphne' DEVE ser o primeiro aplicativo da lista.
INSTALLED_APPS = [
    'daphne',
    'channels',
    'scara_app',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'scara_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Esta linha é CRUCIAL. Ela diz ao Django para usar o nosso "porteiro" ASGI.
ASGI_APPLICATION = 'scara_project.asgi.application'

DATABASES = { 'default': { 'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3' } }
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuração de LOGGING para forçar a exibição de todas as mensagens de diagnóstico.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': { 'console': { 'class': 'logging.StreamHandler' } },
    'root': { 'handlers': ['console'], 'level': 'INFO' },
}

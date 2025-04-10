"""
Django settings for educational_platform project.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-u^e$!+nyn%n(c3%*=f09#k(0!g#82xm*8_rw=0&!g9lk5pbs(5'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['0.0.0.0', 'localhost', '127.0.0.1', 'dd7133e5-0784-467d-88f8-1237e43ae485-00-2c1y8rxcc28wd.worf.replit.dev', '.replit.dev', '.repl.co']

# Base URL для генерации абсолютных ссылок
BASE_URL = 'https://dd7133e5-0784-467d-88f8-1237e43ae485-00-2c1y8rxcc28wd.worf.replit.dev'

# CSRF protection settings
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SAMESITE = None
SESSION_COOKIE_SAMESITE = None
CSRF_TRUSTED_ORIGINS = [
    'https://dd7133e5-0784-467d-88f8-1237e43ae485-00-2c1y8rxcc28wd.worf.replit.dev',
    'https://*.replit.dev',
    'https://*.repl.co',
    'http://dd7133e5-0784-467d-88f8-1237e43ae485-00-2c1y8rxcc28wd.worf.replit.dev',
    'http://*.replit.dev',
    'http://*.repl.co',
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Собственные приложения
    'users.apps.UsersConfig',
    'courses.apps.CoursesConfig',
    'lessons.apps.LessonsConfig',
    'assignments.apps.AssignmentsConfig',
    'gamification.apps.GamificationConfig',
    'ai_assistant.apps.AiAssistantConfig',
    'olympiads.apps.OlympiadsConfig',
    'dashboard.apps.DashboardConfig',
    'notifications.apps.NotificationsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # Заменяем стандартный CSRF-middleware на наш кастомный
    'educational_platform.csrf_hack.CustomCsrfMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',  # закомментировано, т.к. используем кастомный
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Эти настройки уже включены выше

ROOT_URLCONF = 'educational_platform.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'educational_platform.wsgi.application'

# Database
# PostgreSQL configuration
import os
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('PGDATABASE'),
        'USER': os.environ.get('PGUSER'),
        'PASSWORD': os.environ.get('PGPASSWORD'),
        'HOST': os.environ.get('PGHOST'),
        'PORT': os.environ.get('PGPORT'),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# User model customization
AUTH_USER_MODEL = 'users.CustomUser'

# Login redirect
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'
LOGIN_URL = 'login'

# CSRF settings
CSRF_FAILURE_VIEW = 'educational_platform.csrf_hack.csrf_failure_view'
CSRF_COOKIE_SECURE = not DEBUG  # Включаем только для production
CSRF_USE_SESSIONS = False       # Храним CSRF токен в cookie
CSRF_COOKIE_HTTPONLY = False    # Разрешаем доступ к куки из JavaScript

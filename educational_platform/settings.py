"""
Django settings for educational_platform project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Загрузка переменных из .env файла
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-u^e$!+nyn%n(c3%*=f09#k(0!g#82xm*8_rw=0&!g9lk5pbs(5')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '0.0.0.0,localhost,127.0.0.1,testserver').split(',')
ALLOWED_HOSTS.append('f483f18e-7fb8-4ed3-a030-6826aa63f5d3-00-18gt2om9wenpq.pike.replit.dev')
ALLOWED_HOSTS.extend(['.replit.dev', '.repl.co'])

# Base URL для генерации абсолютных ссылок
BASE_URL = os.environ.get('BASE_URL', 'http://localhost:8000')

# CSRF protection settings
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SAMESITE = None
SESSION_COOKIE_SAMESITE = None

# Формируем CSRF_TRUSTED_ORIGINS из BASE_URL
base_url = BASE_URL.strip()
if base_url:
    CSRF_TRUSTED_ORIGINS = [
        f"https://{base_url.replace('https://', '').replace('http://', '')}",
        f"http://{base_url.replace('https://', '').replace('http://', '')}"
    ]
    # Добавляем общие домены
    CSRF_TRUSTED_ORIGINS.extend([
        'https://*.replit.dev',
        'https://*.repl.co',
        'http://*.replit.dev',
        'http://*.repl.co',
    ])
else:
    CSRF_TRUSTED_ORIGINS = [
        'https://*.replit.dev',
        'https://*.repl.co',
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
    # Сторонние приложения
    'markdownify.apps.MarkdownifyConfig',
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

# Настройки Markdownify
MARKDOWNIFY = {
    'default': {
        'MARKDOWN_EXTENSIONS': [
            'markdown.extensions.fenced_code',
            'markdown.extensions.codehilite',
            'markdown.extensions.tables',
            'markdown.extensions.toc',
            'mdx_math',  # LaTeX поддержка
        ],
        'WHITELIST_TAGS': [
            'a', 'abbr', 'b', 'blockquote', 'br', 'code', 'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'hr', 'i', 'img', 'li', 'ol', 'p', 'pre', 'strong', 'table', 'tbody', 'td', 'th', 'thead',
            'tr', 'ul', 'div', 'span', 'math',
        ],
        'WHITELIST_ATTRS': [
            'href', 'src', 'alt', 'title', 'class', 'style', 'id',
        ],
        'WHITELIST_STYLES': [
            'width', 'height', 'margin', 'padding', 'color', 'background-color', 'text-align',
            'border', 'font-weight', 'font-size', 'font-family',
        ],
    }
}

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
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('PGDATABASE', 'postgres'),
        'USER': os.environ.get('PGUSER', 'postgres'),
        'PASSWORD': os.environ.get('PGPASSWORD', ''),
        'HOST': os.environ.get('PGHOST', 'localhost'),
        'PORT': os.environ.get('PGPORT', '5432'),
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
TIME_ZONE = 'Asia/Yekaterinburg'  # UTC+5
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

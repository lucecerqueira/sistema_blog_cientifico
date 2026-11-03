from pathlib import Path
import os
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    USE_POSTGRES=(bool, True),
)
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('DJANGO_SECRET_KEY', default='fallback-secret-key-change-in-production')
DEBUG = env('DJANGO_DEBUG')
ALLOWED_HOSTS = env.list('DJANGO_ALLOWED_HOSTS', default=['*'])

# Configuração de Proxy Reverso e HTTPS no Render
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

SITE_ID = 1

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # Third-party apps
    'rest_framework',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',
    
    # Local apps
    'ds_platform',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'core_config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
            BASE_DIR / 'ds_platform' / 'templates',
        ],
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

WSGI_APPLICATION = 'core_config.wsgi.application'

# Configuração Híbrida PostgreSQL com Fallback para SQLite
if env('USE_POSTGRES'):
    try:
        import psycopg2
        DATABASES = {
            'default': env.db('DATABASE_URL', default='postgres://postgres:postgres@localhost:5432/datascience_db')
        }
    except Exception:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_USER_MODEL = 'ds_platform.User'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/redirecionar-acesso/'
LOGOUT_REDIRECT_URL = '/'

# Configurações do Django Allauth
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'

# Comportamento do Login Social
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_STORE_TOKENS = False

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'APP': {
            'client_id': env('GOOGLE_CLIENT_ID', default='dummy-google-id'),
            'secret': env('GOOGLE_CLIENT_SECRET', default='dummy-google-secret'),
            'key': ''
        }
    },
    'github': {
        'SCOPE': ['user', 'repo'],
        'APP': {
            'client_id': env('GITHUB_CLIENT_ID', default='dummy-github-id'),
            'secret': env('GITHUB_CLIENT_SECRET', default='dummy-github-secret'),
            'key': ''
        }
    }
}

# Configuração de E-mail
EMAIL_HOST_USER_VAL = env('EMAIL_HOST_USER', default='')
if EMAIL_HOST_USER_VAL and EMAIL_HOST_USER_VAL != 'seu_email_profissional@gmail.com':
    EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
    EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
    EMAIL_PORT = env.int('EMAIL_PORT', default=587)
    EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
    EMAIL_HOST_USER = EMAIL_HOST_USER_VAL
    EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
    DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER_VAL)
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'noreply@datascience.pro'

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Compressão e armazenamento de arquivos estáticos pelo WhiteNoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CSRF_TRUSTED_ORIGINS = [
    'https://sistema-blog-cientifico.onrender.com',
    'http://127.0.0.1:8040',
    'http://localhost:8040',
    'http://0.0.0.0:8040',
]
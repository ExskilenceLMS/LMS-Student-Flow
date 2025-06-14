"""
Django settings for LMS_Project project.

Generated by 'django-admin startproject' using Django 4.1.13.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

from pathlib import Path
from decouple import config
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY =  config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = ['*']

import os

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} [{levelname}] {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'django.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        # Your app's logger - keep INFO and above
        'Student_Flow_App': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        # Django default logger - keep WARNING and above to reduce noise
        'django': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': True,
        },
        # Azure SDK logger - suppress info/debug logs by raising level to WARNING or ERROR
        'azure.core.pipeline.policies.http_logging_policy': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': False,
        },
        # Root logger fallback
        '': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
        },
    },
}

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework', 
    'djongo',
    'Student_Flow_App',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
]
# from urllib.parse import quote_plus
# uname = config('MONGO_USER')
# pwd =  config('MONGO_PASSWORD')
# host = config('MONGO_HOST')
# Db = config('MONGO_DB_NAME')
# authMechanism = config('MONGO_AUTH_MECHANISM')
# escaped_username = quote_plus(uname)
# escaped_password = quote_plus(pwd)
# print('escaped_username',escaped_username)
# print('escaped_password',escaped_password)

# uri = config('MONGO_CONNECTION_STRING')
DATABASES = {
    'mongodb': {
        'ENGINE': 'djongo',

        # 'NAME': 'LMSmongodb',
        # 'CLIENT': {
        #     'host': 'mongodb+srv://kecoview:FVy5fqqCtQy3KIt6@cluster0.b9wmlid.mongodb.net/',
        #     'username': 'kecoview',
        #     'password': 'FVy5fqqCtQy3KIt6',
        #     'authMechanism': 'SCRAM-SHA-1',
        # }
        'NAME':   config('MONGO_DB_NAME'),
        'ENFORCE_SCHEMA': False,  
        'CLIENT': {
            'host': config('MONGO_CONNECTION_STRING'),
            'username':  config('MONGO_USER'),
            'password':  config('MONGO_PASSWORD'),
            'authMechanism':  config('MONGO_AUTH_MECHANISM'),
        }
    },
    'default': {
        'ENGINE': 'mssql',
        'NAME': config('DB_NAME'),
        # 'NAME': 'staging',
        'USER':  config('DB_USER'), 
        'PASSWORD':  config('DB_PASSWORD'), 
        'HOST':  config('DB_HOST'), 
        'PORT': '1433',
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
            'trustServerCertificate': 'yes',  # Add this to avoid SSL errors
        },
    }
}

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'https://staging-exskilence.azurewebsites.net',
    'https://live-exskilence.azurewebsites.net',
 
]

CSRF_TRUSTED_ORIGINS=[ 
    'http://localhost:3000',
     'https://staging-exskilence.azurewebsites.net',
     'https://live-exskilence.azurewebsites.net',
    ]

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config('REDIS_CONNECTION_STRING'),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}
ROOT_URLCONF = 'LMS_Project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'LMS_Project.wsgi.application'

AZURE_ACCOUNT_NAME = config('AZURE_ACCOUNT_NAME')
AZURE_ACCOUNT_KEY = config('AZURE_ACCOUNT_KEY')
AZURE_CONTAINER =  config('AZURE_CONTAINER')

MIGRATION_MODULES = {
    'LMS_Mongodb_App': None,
    'LMS_MSSQLdb_App': None
}
MSSQL_SERVER_NAME =  config('MSSQL_SERVER_NAME')
MSSQL_DATABASE_NAME =  config('MSSQL_DATABASE_NAME')
MSSQL_USERNAME =  config('MSSQL_USERNAME')
MSSQL_PWD =  config('MSSQL_PWD')
MSSQL_DRIVER =      config('MSSQL_DRIVER')


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

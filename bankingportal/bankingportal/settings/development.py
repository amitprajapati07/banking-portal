"""Development settings — inherits from base."""

from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

# Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# More verbose DB query logging in development
LOGGING["loggers"]["django.db.backends"]["level"] = "DEBUG"  # noqa: F405

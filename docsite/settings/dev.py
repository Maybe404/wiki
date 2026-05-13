import os

from .base import *  # noqa: F401, F403

DEBUG = True
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-key-do-not-use-in-production-change-me-now")
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

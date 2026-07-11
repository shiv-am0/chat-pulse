from .base import *
from decouple import config

DEBUG = False

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='api.chatpulse.online,localhost',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='https://chatpulse.online',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# ── HTTPS / Security Headers ────────────────────────────────
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# ── Trusted origins for CSRF ─────────────────────────────────
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='https://chatpulse.online',
    cast=lambda v: [s.strip() for s in v.split(',') if s.strip()]
)

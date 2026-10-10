"""Fail-closed production configuration shared by web and model processes."""

import hashlib
import os

from django.core.exceptions import ImproperlyConfigured


DEVELOPMENT_SECRET_KEY = "django-insecure-zm^1_^i5)3gp^&0io6zg72&z!a*d=9kf9o2%uft+27l)+t(#3e"


def deployment_settings(config, environ=None):
    env = os.environ if environ is None else environ
    mode = env.get("JB_DEPLOYMENT_MODE", "local").strip().lower()
    if mode not in {"local", "production"}:
        raise ImproperlyConfigured("JB_DEPLOYMENT_MODE must be local or production")
    if mode == "local":
        debug_value = config.get("DEBUG", False)
        return {
            "SECRET_KEY": config.get("SECRET_KEY") or DEVELOPMENT_SECRET_KEY,
            "ALLOWED_HOSTS": ["*"],
            "DEBUG": str(debug_value).strip().lower() in {"true", "1", "yes", "on"},
        }

    required = ("JB_SECRET_KEY", "JB_DB_PASSWORD", "JB_REDIS_PASSWORD", "JB_DEFAULT_PASSWORD", "JB_ALLOWED_HOSTS")
    missing = [name for name in required if not str(env.get(name, "")).strip()]
    if missing:
        raise ImproperlyConfigured("Production deployment requires: " + ", ".join(missing))

    secret_key = env["JB_SECRET_KEY"]
    if len(secret_key) < 32 or secret_key.startswith("django-insecure-"):
        raise ImproperlyConfigured("JB_SECRET_KEY must be a unique, non-development key of at least 32 characters")
    if env["JB_DEFAULT_PASSWORD"] == "TelecomAI@123..":
        raise ImproperlyConfigured("JB_DEFAULT_PASSWORD must differ from the bundled development default")
    if (
        hashlib.sha256(env["JB_DB_PASSWORD"].encode()).hexdigest()
        == "9efb9dca79d0a284f9a1a774279ae217d815c948c23e80d055aec5549cf11a28"
        or hashlib.sha256(env["JB_REDIS_PASSWORD"].encode()).hexdigest()
        == "3aab48d7fbbeb6e9f890ac1f7b51182325d21978036e24def6653f44e08148c3"
    ):
        raise ImproperlyConfigured("Database and Redis passwords must differ from bundled development defaults")
    hosts = [host.strip() for host in env["JB_ALLOWED_HOSTS"].split(",") if host.strip()]
    if not hosts or any(host in {"*", "localhost", "127.0.0.1"} for host in hosts):
        raise ImproperlyConfigured("JB_ALLOWED_HOSTS must list explicit non-local hosts")
    if str(env.get("JB_DEBUG", "false")).strip().lower() not in {"false", "0", "no", "off"}:
        raise ImproperlyConfigured("JB_DEBUG must be false in production")

    return {
        "SECRET_KEY": secret_key,
        "ALLOWED_HOSTS": hosts,
        "DEBUG": False,
        "SESSION_COOKIE_SECURE": True,
        "CSRF_COOKIE_SECURE": True,
        "SECURE_SSL_REDIRECT": True,
        "SECURE_HSTS_SECONDS": 3600,
        "SECURE_CONTENT_TYPE_NOSNIFF": True,
    }

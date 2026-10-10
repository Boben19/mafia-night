import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent

def _load_env(path):
    # tiny .env reader so keys stay out of the code; real environment variables win
    try:
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("\"'"))
    except FileNotFoundError:
        pass

_load_env(BASE_DIR / ".env")
SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-before-you-deploy")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = ["127.0.0.1", "localhost", ".pythonanywhere.com"]

INSTALLED_APPS = ["django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles", "django.contrib.sites", "allauth", "allauth.account", "allauth.socialaccount",
    "allauth.socialaccount.providers.google", "allauth.socialaccount.providers.facebook",
    "allauth.socialaccount.providers.github", "game"]

MIDDLEWARE = ["django.middleware.security.SecurityMiddleware", "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware", "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware", "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware", "allauth.account.middleware.AccountMiddleware"]
    
ROOT_URLCONF = "mafia.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [BASE_DIR / "templates"], "APP_DIRS": True,
    "OPTIONS": {"context_processors": ["django.template.context_processors.debug", "django.template.context_processors.request",
    "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION = "mafia.wsgi.application"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
TIME_ZONE = "Asia/Manila"
USE_TZ = True
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SITE_ID = 1
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend", "allauth.account.auth_backends.AuthenticationBackend"]
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/accounts/login/"
ACCOUNT_LOGIN_METHODS = {"username", "email"}
ACCOUNT_SIGNUP_FIELDS = ["username*", "email", "password1*", "password2*"]
ACCOUNT_LOGOUT_ON_GET = True
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_AUTO_SIGNUP = True

ACCOUNT_EMAIL_VERIFICATION = "none"
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "http" if DEBUG else "https"

# Live site on PythonAnywhere
CSRF_TRUSTED_ORIGINS = ["https://bobennn.pythonanywhere.com"]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Keys come from environment variables, never from this file.
# A provider's button only shows once its ID is set.
SOCIALACCOUNT_PROVIDERS = {}
for _p in ("github", "google", "facebook"):
    if os.environ.get(_p.upper() + "_ID"):
        SOCIALACCOUNT_PROVIDERS[_p] = {"APP": {
            "client_id": os.environ[_p.upper() + "_ID"],
            "secret": os.environ.get(_p.upper() + "_SECRET", ""),
            "key": "",
        }}
if "github" in SOCIALACCOUNT_PROVIDERS:
    SOCIALACCOUNT_PROVIDERS["github"]["SCOPE"] = ["user", "user:email"]

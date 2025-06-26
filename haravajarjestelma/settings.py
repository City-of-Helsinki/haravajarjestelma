import os
import subprocess

import environ
import sentry_sdk
from django.utils.translation import gettext_lazy as _
from sentry_sdk.integrations.django import DjangoIntegration

checkout_dir = environ.Path(__file__) - 2
assert os.path.exists(checkout_dir("manage.py"))

parent_dir = checkout_dir.path("..")
if os.path.isdir(parent_dir("etc")):
    env_file = parent_dir("etc/env")
    default_var_root = environ.Path(parent_dir("var"))
else:
    env_file = checkout_dir(".env")
    default_var_root = environ.Path(checkout_dir("var"))

env = environ.Env(
    DEBUG=(bool, False),
    TIER=(str, "dev"),  # one of: prod, qa, stage, test, dev
    SECRET_KEY=(str, ""),
    MEDIA_ROOT=(environ.Path(), default_var_root("media")),
    STATIC_ROOT=(environ.Path(), default_var_root("static")),
    MEDIA_URL=(str, "/media/"),
    STATIC_URL=(str, "/static/"),
    ALLOWED_HOSTS=(list, []),
    DATABASE_URL=(
        str,
        "postgis://haravajarjestelma:haravajarjestelma@localhost/haravajarjestelma",
    ),
    DATABASE_PASSWORD=(str, ""),
    CACHE_URL=(str, "locmemcache://"),
    DEFAULT_FROM_EMAIL=(str, "haravajarjestelma@example.com"),
    MAILER_EMAIL_BACKEND=(str, "django.core.mail.backends.console.EmailBackend"),
    # None == django-mailer uses internal default
    MAILER_LOCK_PATH=(str, None),
    MAIL_MAILGUN_KEY=(str, ""),
    MAIL_MAILGUN_DOMAIN=(str, ""),
    MAIL_MAILGUN_API=(str, ""),
    MAIL_SENDGRID_KEY=(str, ""),
    SENTRY_DSN=(str, ""),
    SENTRY_ENVIRONMENT=(str, ""),
    CORS_ORIGIN_WHITELIST=(list, []),
    CORS_ORIGIN_ALLOW_ALL=(bool, False),
    OIDC_API_AUTHORIZATION_FIELD=(list, []),
    OIDC_API_SCOPE_PREFIX=(list, []),
    OIDC_AUDIENCE=(list, []),
    OIDC_ISSUER=(list, []),
    OIDC_REQUIRE_SCOPE_FOR_AUTHENTICATION=(bool, False),
    EVENT_MINIMUM_DAYS_BEFORE_START=(int, 7),
    EVENT_MAXIMUM_COUNT_PER_CONTRACT_ZONE=(int, 3),
    EVENT_REMINDER_DAYS_IN_ADVANCE=(int, 2),
    HELSINKI_WFS_BASE_URL=(str, "https://kartta.hel.fi/ws/geoserver/avoindata/wfs"),
    EXCLUDED_CONTRACT_ZONES=(list, []),
    DIGITRANSIT_ADDRESS_SEARCH_URL=(
        str,
        "https://api.digitransit.fi/geocoding/v1/search",
    ),
    DIGITRANSIT_API_KEY=(str, ""),
    LOG_LEVEL=(str, "INFO"),
    GDPR_API_QUERY_SCOPE=(str, "gdprquery"),
    GDPR_API_DELETE_SCOPE=(str, "gdprdelete"),
)
if os.path.exists(env_file):
    env.read_env(env_file)

BASE_DIR = str(checkout_dir)

DEBUG = env.bool("DEBUG")
TIER = env.str("TIER")
SECRET_KEY = env.str("SECRET_KEY")
if DEBUG and not SECRET_KEY:
    SECRET_KEY = "xxx"

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

DATABASES = {"default": env.db()}
# Ensure postgis engine
DATABASES["default"]["ENGINE"] = "django.contrib.gis.db.backends.postgis"
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

if env("DATABASE_PASSWORD"):
    DATABASES["default"]["PASSWORD"] = env("DATABASE_PASSWORD")

CACHES = {"default": env.cache()}

if env.str("DEFAULT_FROM_EMAIL"):
    DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL")

EMAIL_BACKEND = "mailer.backend.DbBackend"
MAILER_EMAIL_BACKEND = env.str("MAILER_EMAIL_BACKEND")
MAILER_LOCK_PATH = env("MAILER_LOCK_PATH")

if MAILER_EMAIL_BACKEND == "anymail.backends.mailgun.EmailBackend":
    ANYMAIL = {
        "MAILGUN_API_KEY": env("MAIL_MAILGUN_KEY"),
        "MAILGUN_SENDER_DOMAIN": env("MAIL_MAILGUN_DOMAIN"),
        "MAILGUN_API_URL": env("MAIL_MAILGUN_API"),
    }
elif MAILER_EMAIL_BACKEND == "anymail.backends.sendgrid.EmailBackend":
    ANYMAIL = {"SENDGRID_API_KEY": env.str("MAIL_SENDGRID_KEY")}

try:
    version = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).strip()
except Exception:
    version = "n/a"

sentry_sdk.init(
    dsn=env.str("SENTRY_DSN"),
    release=version,
    environment=env("SENTRY_ENVIRONMENT"),
    integrations=[DjangoIntegration()],
)

MEDIA_ROOT = env("MEDIA_ROOT")
STATIC_ROOT = env("STATIC_ROOT")
MEDIA_URL = env.str("MEDIA_URL")
STATIC_URL = env.str("STATIC_URL")

ROOT_URLCONF = "haravajarjestelma.urls"
WSGI_APPLICATION = "haravajarjestelma.wsgi.application"

LANGUAGE_CODE = "en"
LANGUAGES = (("fi", _("Finnish")), ("sv", _("Swedish")), ("en", _("English")))
TIME_ZONE = "Europe/Helsinki"
USE_I18N = True
USE_L10N = True
USE_TZ = True

LOCALE_PATHS = (os.path.join(BASE_DIR, "locale"),)

INSTALLED_APPS = [
    "helusers.apps.HelusersConfig",
    "helusers.apps.HelusersAdminConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "rest_framework",
    "rest_framework_gis",
    "corsheaders",
    "munigeo",
    "django_filters",
    "parler",
    "anymail",
    "mailer",
    "events",
    "users",
    "areas",
    "django_ilmoitin",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

SITE_ID = 1

AUTH_USER_MODEL = "users.User"

DEFAULT_SRID = 4326

PARLER_LANGUAGES = {SITE_ID: ({"code": "fi"},)}

EVENT_MINIMUM_DAYS_BEFORE_START = env("EVENT_MINIMUM_DAYS_BEFORE_START")
EVENT_MAXIMUM_COUNT_PER_CONTRACT_ZONE = env("EVENT_MAXIMUM_COUNT_PER_CONTRACT_ZONE")
EVENT_REMINDER_DAYS_IN_ADVANCE = env("EVENT_REMINDER_DAYS_IN_ADVANCE")

HELSINKI_WFS_BASE_URL = env("HELSINKI_WFS_BASE_URL")

EXCLUDED_CONTRACT_ZONES = env("EXCLUDED_CONTRACT_ZONES")

DIGITRANSIT_ADDRESS_SEARCH_URL = env("DIGITRANSIT_ADDRESS_SEARCH_URL")
DIGITRANSIT_API_KEY = env("DIGITRANSIT_API_KEY")

CORS_ORIGIN_WHITELIST = env("CORS_ORIGIN_WHITELIST")
CORS_ORIGIN_ALLOW_ALL = env("CORS_ORIGIN_ALLOW_ALL")

OIDC_API_TOKEN_AUTH = {
    "AUDIENCE": env("OIDC_AUDIENCE"),
    "API_SCOPE_PREFIX": env("OIDC_API_SCOPE_PREFIX"),
    "ISSUER": env("OIDC_ISSUER"),
    "API_AUTHORIZATION_FIELD": env("OIDC_API_AUTHORIZATION_FIELD"),
    "REQUIRE_API_SCOPE_FOR_AUTHENTICATION": env(
        "OIDC_REQUIRE_SCOPE_FOR_AUTHENTICATION"
    ),
}

HELUSERS_BACK_CHANNEL_LOGOUT_ENABLED = True

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 100,
    "DEFAULT_AUTHENTICATION_CLASSES": ("helusers.oidc.ApiTokenAuthentication",),
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
}

LOG_LEVEL = env("LOG_LEVEL")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "timestamped_named": {
            "format": "%(asctime)s %(name)s %(levelname)s: %(message)s"
        }
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "timestamped_named"}
    },
    "loggers": {"": {"handlers": ["console"], "level": LOG_LEVEL}},
}

# local_settings.py can be used to override settings
local_settings_path = os.path.join(checkout_dir(), "local_settings.py")
if os.path.exists(local_settings_path):
    with open(local_settings_path) as fp:
        code = compile(fp.read(), local_settings_path, "exec")
    exec(code, globals(), locals())

# GDPR API settings
GDPR_API_MODEL = "users.User"
GDPR_API_MODEL_LOOKUP = "uuid"
GDPR_API_URL_PATTERN = "v1/user/<uuid:uuid>"
GDPR_API_USER_PROVIDER = "users.gdpr.get_user"
GDPR_API_DELETER = "users.gdpr.delete_data"
GDPR_API_QUERY_SCOPE = env("GDPR_API_QUERY_SCOPE")
GDPR_API_DELETE_SCOPE = env("GDPR_API_DELETE_SCOPE")

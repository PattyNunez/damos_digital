"""
Django settings for config project.
"""

from pathlib import Path

import environ
import pillow_heif

# Los técnicos suben fotos desde el celular — iPhone guarda por defecto en HEIC/HEIF, formato
# que Pillow no reconoce de fábrica. Sin esto, cualquier ImageField (FotoChecklist, FotoHallazgo,
# etc.) rechaza esas fotos con "no era una imagen o estaba corrupta", aunque sí lo sea. Se
# registra acá (no en un solo AppConfig.ready()) para cubrir todos los ImageField de una vez,
# apenas arranca el proceso.
pillow_heif.register_heif_opener()

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="django-insecure-change-me")

DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# Render inyecta esta variable automáticamente con el dominio *.onrender.com asignado — se
# agrega sola a ALLOWED_HOSTS/CSRF_TRUSTED_ORIGINS sin que haya que hardcodear el dominio ni
# repetirlo a mano en la variable ALLOWED_HOSTS del dashboard.
RENDER_EXTERNAL_HOSTNAME = env("RENDER_EXTERNAL_HOSTNAME", default=None)
CSRF_TRUSTED_ORIGINS = []
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")

# Render (como casi todo PaaS) termina el TLS en su proxy y reenvía por HTTP interno con este
# header — sin esto, Django cree que toda request es HTTP aunque el visitante esté en https://,
# lo que rompe cosas que dependen de saber si la conexión es segura.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # cloudinary_storage/cloudinary van DESPUÉS de staticfiles a propósito: los usamos solo
    # para archivos MEDIA (fotos, PDFs) — los estáticos (CSS/JS) siguen siendo de WhiteNoise.
    # El orden importa: django-cloudinary-storage pisa collectstatic si va antes.
    "cloudinary_storage",
    "cloudinary",
    # apps del dominio Damol
    "cuentas",
    "clientes",
    "equipos",
    "catalogos",
    "inventario",
    "servicios",
    "cotizaciones",
    "personal",
    "checklist",
    "mediciones",
    "reportes",
    "dashboard",
]

LOGIN_URL = "cuentas:login"
LOGIN_REDIRECT_URL = "inicio"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

if env("DATABASE_URL", default=None):
    # Render (y la mayoría de PaaS) inyectan la conexión completa como una sola URL.
    DATABASES = {"default": env.db("DATABASE_URL")}
else:
    # Desarrollo local: variables sueltas, como ya las trae .env.example.
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME", default="damol_digital"),
            "USER": env("DB_USER", default="damol_digital"),
            "PASSWORD": env("DB_PASSWORD", default="damol_digital"),
            "HOST": env("DB_HOST", default="localhost"),
            "PORT": env("DB_PORT", default="5432"),
        }
    }


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "es"

TIME_ZONE = "America/Lima"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # adonde collectstatic junta todo; WhiteNoise sirve desde acá

# WhiteNoise: comprime y cachea los estáticos con hash en el nombre, para que el navegador los
# guarde en caché para siempre sin arriesgarse a servir una versión vieja tras un deploy.
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Media files (fotos de checklist, firmas, certificados, informes PDF generados): en Cloudinary,
# no en el disco local — el disco de Render (plan gratuito) no es persistente, se pierde en
# cada redeploy/reinicio. MEDIA_URL/MEDIA_ROOT ya no importan para servir nada (Cloudinary
# devuelve su propia URL absoluta), pero se dejan por si algo local los sigue leyendo.
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Todo ImageField que NO tenga un storage explícito (fotos de checklist/hallazgos, logos,
# firmas) usa esta por defecto. Los FileField "raw" (PDFs, certificados) necesitan la otra
# clase (RawMediaCloudinaryStorage) — Cloudinary distingue resource_type=image vs raw, así que
# no sirve una sola clase para todo; se asigna explícitamente en cada uno de esos 4 campos.
DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

# Credenciales: una sola variable, formato estándar de Cloudinary — se lee sola del entorno
# (cloudinary.config() la detecta automáticamente), no hace falta declarar CLOUDINARY_STORAGE acá.
# Ver .env.example para el formato exacto.

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Endurecimiento de producción: solo activo cuando DEBUG=False (Render), nunca en desarrollo
# local — señalado por `manage.py check --deploy` al preparar el despliegue.
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True

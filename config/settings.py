"""
Réglages du projet Django.
Seules les parties marquées (A MODIFIER) vous concernent vraiment.
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Réglages de DÉVELOPPEMENT : ne pas utiliser tels quels sur un vrai serveur.
SECRET_KEY = "cle-de-developpement-a-changer-en-production"
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# Les "applications" actives. "hotel" est NOTRE application.
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "hotel",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "hotel.context.parametres_hotel",   # nom de l'hôtel et devise dans tous les templates
    ]},
}]

WSGI_APPLICATION = "config.wsgi.application"

# BASE DE DONNÉES : SQLite = un simple fichier db.sqlite3, sans rien à installer.
DATABASES = {"default": {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": BASE_DIR / "db.sqlite3",
}}

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Tunis"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
MEDIA_URL = "media/"                 # photos des chambres envoyées par l'administrateur
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Connexion de l'administrateur
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "accueil"

# (A MODIFIER) Affichés sur le site
NOM_HOTEL = "Hôtel de Luxe"
DEVISE = "DT"                        # mettre "€" si vous préférez

"""Variables disponibles automatiquement dans TOUS les templates."""
from django.conf import settings


def parametres_hotel(request):
    return {"NOM_HOTEL": settings.NOM_HOTEL, "DEVISE": settings.DEVISE}

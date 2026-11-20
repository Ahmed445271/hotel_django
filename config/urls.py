"""Table des adresses principales : on délègue tout à l'application 'hotel'."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),   # interface d'administration fournie gratuitement par Django
    path("", include("hotel.urls")),
]

# En développement, Django sert lui-même les photos envoyées
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

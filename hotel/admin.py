"""Interface d'administration automatique de Django (adresse : /admin/)."""
from django.contrib import admin

from .models import Chambre, Client, Reservation


@admin.register(Chambre)
class ChambreAdmin(admin.ModelAdmin):
    list_display = ("num_chambre", "type_chambre", "prix_nuit")
    list_filter = ("type_chambre",)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("id", "nom", "prenom", "telephone")
    search_fields = ("nom", "prenom", "telephone")


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "chambre", "date_debut", "date_fin", "prix_total")

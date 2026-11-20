"""Adresses de l'application : quelle adresse (URL) appelle quelle vue."""
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    # Pages publiques
    path("", views.accueil, name="accueil"),
    path("chambres/", views.liste_chambres, name="liste_chambres"),
    path("chambres/<int:pk>/", views.detail_chambre, name="detail_chambre"),

    # Connexion du personnel
    path("connexion/", auth_views.LoginView.as_view(), name="login"),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="logout"),

    # Personnel
    path("tableau-de-bord/", views.dashboard, name="dashboard"),

    path("gestion/chambres/", views.gestion_chambres, name="gestion_chambres"),
    path("gestion/chambres/ajouter/", views.ChambreCreate.as_view(), name="chambre_ajouter"),
    path("gestion/chambres/<int:pk>/modifier/", views.ChambreUpdate.as_view(), name="chambre_modifier"),
    path("gestion/chambres/<int:pk>/supprimer/", views.ChambreDelete.as_view(), name="chambre_supprimer"),

    path("gestion/clients/", views.gestion_clients, name="gestion_clients"),
    path("gestion/clients/ajouter/", views.ClientCreate.as_view(), name="client_ajouter"),
    path("gestion/clients/<int:pk>/modifier/", views.ClientUpdate.as_view(), name="client_modifier"),
    path("gestion/clients/<int:pk>/supprimer/", views.ClientDelete.as_view(), name="client_supprimer"),

    path("gestion/reservations/", views.gestion_reservations, name="gestion_reservations"),
    path("gestion/reservations/ajouter/", views.ReservationCreate.as_view(), name="reservation_ajouter"),
    path("gestion/reservations/<int:pk>/liberer/", views.reservation_liberer, name="reservation_liberer"),
    path("gestion/reservations/<int:pk>/annuler/", views.reservation_annuler, name="reservation_annuler"),
]

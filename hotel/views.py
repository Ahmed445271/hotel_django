"""
views.py : LES PAGES
Une "vue" reçoit une requête du navigateur et renvoie une page HTML.
Schéma : navigateur -> urls.py -> vue -> modèles (base de données) -> template HTML.

Pages publiques : accueil, liste des chambres, détails d'une chambre (+ réservation).
Pages du personnel (connexion obligatoire) : tableau de bord et gestion complète.
"""
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, UpdateView

from .forms import ChambreForm, ClientForm, ReservationForm, ReservationRapideForm
from .models import Chambre, Client, Reservation, aujourdhui
from .statistiques import calculer_statistiques, clients_fideles

# Décorateur pour les vues-fonctions réservées au personnel (is_staff)
personnel_requis = user_passes_test(lambda u: u.is_staff, login_url="login")


class PersonnelMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Même protection pour les vues-classes."""
    def test_func(self):
        return self.request.user.is_staff


def retour(request, defaut):
    """Redirige vers la page d'où vient l'action (champ caché 'next'), sinon vers 'defaut'."""
    suivant = request.POST.get("next", "")
    if suivant and url_has_allowed_host_and_scheme(suivant, allowed_hosts={request.get_host()}):
        return redirect(suivant)
    return redirect(defaut)


# ======================================================================
# PAGES PUBLIQUES
# ======================================================================

def accueil(request):
    libres = Chambre.objects.avec_statut().filter(occupee=False)[:3]
    return render(request, "hotel/accueil.html",
                  {"chambres": libres, "stats": calculer_statistiques()})


def liste_chambres(request):
    chambres = Chambre.objects.avec_statut()
    type_choisi = request.GET.get("type", "")
    statut = request.GET.get("statut", "")
    if type_choisi in dict(Chambre.TYPES):
        chambres = chambres.filter(type_chambre=type_choisi)
    if statut == "libre":
        chambres = chambres.filter(occupee=False)
    elif statut == "occupee":
        chambres = chambres.filter(occupee=True)
    return render(request, "hotel/chambres.html", {
        "chambres": chambres, "types": Chambre.TYPES,
        "type_choisi": type_choisi, "statut": statut})


def detail_chambre(request, pk):
    chambre = get_object_or_404(Chambre.objects.avec_statut(), pk=pk)
    if request.method == "POST":
        form = ReservationRapideForm(request.POST, chambre=chambre)
        if form.is_valid():
            reservation = form.enregistrer()
            messages.success(
                request,
                f"Réservation {reservation.numero} confirmée : chambre {chambre.num_chambre}, "
                f"du {reservation.date_debut:%d/%m/%Y} au {reservation.date_fin:%d/%m/%Y} "
                f"({reservation.nb_nuits} nuit(s)).")
            return redirect("detail_chambre", pk=pk)
    else:
        form = ReservationRapideForm(chambre=chambre)
    return render(request, "hotel/chambre_detail.html", {"chambre": chambre, "form": form})


# ======================================================================
# TABLEAU DE BORD (personnel)
# ======================================================================

@personnel_requis
def dashboard(request):
    filtre = request.GET.get("filtre", "tous")
    jour = aujourdhui()
    reservations = Reservation.objects.select_related("client", "chambre")
    if filtre == "confirmees":
        reservations = reservations.filter(date_fin__gt=jour)
    elif filtre == "passees":
        reservations = reservations.filter(date_fin__lte=jour)
    return render(request, "hotel/dashboard.html", {
        "stats": calculer_statistiques(),
        "reservations": reservations[:8],
        "fideles": clients_fideles(),
        "filtre": filtre})


# ======================================================================
# GESTION DES CHAMBRES (personnel)
# ======================================================================

@personnel_requis
def gestion_chambres(request):
    filtre = request.GET.get("filtre", "toutes")
    chambres = Chambre.objects.avec_statut()
    if filtre == "libres":
        chambres = chambres.filter(occupee=False)
    elif filtre == "occupees":
        chambres = chambres.filter(occupee=True)
    return render(request, "hotel/gestion_chambres.html", {"chambres": chambres, "filtre": filtre})


class ChambreCreate(PersonnelMixin, SuccessMessageMixin, CreateView):
    model = Chambre
    form_class = ChambreForm
    template_name = "hotel/form.html"
    success_url = reverse_lazy("gestion_chambres")
    success_message = "Chambre ajoutée."
    extra_context = {"titre": "Ajouter une chambre", "retour": reverse_lazy("gestion_chambres")}


class ChambreUpdate(PersonnelMixin, SuccessMessageMixin, UpdateView):
    model = Chambre
    form_class = ChambreForm
    template_name = "hotel/form.html"
    success_url = reverse_lazy("gestion_chambres")
    success_message = "Chambre modifiée."
    extra_context = {"titre": "Modifier la chambre", "retour": reverse_lazy("gestion_chambres")}


class SuppressionSecurisee(PersonnelMixin, DeleteView):
    """Supprime une chambre ou un client, sauf s'il a une réservation en cours ou à venir.
    Les anciennes réservations (historique) sont supprimées avec lui."""
    template_name = "hotel/confirmer_suppression.html"

    def form_valid(self, form):
        objet = self.object
        if objet.reservations.filter(date_fin__gt=aujourdhui()).exists():
            messages.error(self.request, "Impossible : réservation en cours ou à venir.")
            return redirect(self.success_url)
        objet.reservations.all().delete()
        messages.success(self.request, f"« {objet} » supprimé(e).")
        return super().form_valid(form)


class ChambreDelete(SuppressionSecurisee):
    model = Chambre
    success_url = reverse_lazy("gestion_chambres")


# ======================================================================
# GESTION DES CLIENTS (personnel)
# ======================================================================

@personnel_requis
def gestion_clients(request):
    recherche = request.GET.get("q", "").strip()
    clients = Client.objects.annotate(nb_reservations=Count("reservations"))
    if recherche:
        condition = Q(nom__icontains=recherche) | Q(prenom__icontains=recherche)
        if recherche.isdigit() and len(recherche) < 10:      # recherche par identifiant
            condition |= Q(pk=int(recherche))
        clients = clients.filter(condition)
    return render(request, "hotel/gestion_clients.html", {"clients": clients, "recherche": recherche})


class ClientCreate(PersonnelMixin, SuccessMessageMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = "hotel/form.html"
    success_url = reverse_lazy("gestion_clients")
    success_message = "Client ajouté."
    extra_context = {"titre": "Ajouter un client", "retour": reverse_lazy("gestion_clients")}


class ClientUpdate(PersonnelMixin, SuccessMessageMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = "hotel/form.html"
    success_url = reverse_lazy("gestion_clients")
    success_message = "Client modifié."
    extra_context = {"titre": "Modifier le client", "retour": reverse_lazy("gestion_clients")}


class ClientDelete(SuppressionSecurisee):
    model = Client
    success_url = reverse_lazy("gestion_clients")


# ======================================================================
# GESTION DES RÉSERVATIONS (personnel)
# ======================================================================

@personnel_requis
def gestion_reservations(request):
    toutes = request.GET.get("filtre") == "toutes"
    reservations = Reservation.objects.select_related("client", "chambre")
    if not toutes:    # par défaut : en cours et à venir
        reservations = reservations.filter(date_fin__gt=aujourdhui())
    return render(request, "hotel/gestion_reservations.html",
                  {"reservations": reservations, "toutes": toutes})


class ReservationCreate(PersonnelMixin, SuccessMessageMixin, CreateView):
    model = Reservation
    form_class = ReservationForm
    template_name = "hotel/form.html"
    success_url = reverse_lazy("gestion_reservations")
    success_message = "Réservation enregistrée."
    extra_context = {"titre": "Nouvelle réservation", "retour": reverse_lazy("gestion_reservations")}


@personnel_requis
@require_POST
def reservation_liberer(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    numero = reservation.chambre.num_chambre
    try:
        reservation.liberer()
    except ValidationError as erreur:
        messages.error(request, erreur.messages[0])
    else:
        messages.success(request, f"Chambre {numero} libérée.")
    return retour(request, "gestion_reservations")


@personnel_requis
@require_POST
def reservation_annuler(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    try:
        reservation.annuler()
    except ValidationError as erreur:
        messages.error(request, erreur.messages[0])
    else:
        messages.success(request, "Réservation annulée.")
    return retour(request, "gestion_reservations")

"""Calcul des statistiques (taux d'occupation, revenu...)."""
from django.db.models import Count, Sum

from .models import Chambre, Client, Reservation, aujourdhui


def calculer_statistiques():
    jour = aujourdhui()
    total = Chambre.objects.count()
    occupees = Chambre.objects.avec_statut(jour).filter(occupee=True).count()
    taux = round(occupees / total * 100, 1) if total else 0   # évite la division par 0

    # Réservations dont l'arrivée est dans le mois en cours
    ce_mois = Reservation.objects.filter(date_debut__year=jour.year, date_debut__month=jour.month)
    revenu = ce_mois.aggregate(total=Sum("prix_total"))["total"] or 0

    return {
        "total_chambres": total,
        "chambres_occupees": occupees,
        "chambres_libres": total - occupees,
        "taux_occupation": taux,
        "reservations_mois": ce_mois.count(),
        "revenu_mois": revenu,
        "reservations_actives": Reservation.objects.filter(date_fin__gt=jour).count(),
        "total_clients": Client.objects.count(),
    }


def clients_fideles(limite=3):
    """Les clients avec le plus de réservations (et leurs dépenses totales)."""
    return (Client.objects
            .annotate(nb_reservations=Count("reservations"),
                      depense_totale=Sum("reservations__prix_total"))
            .filter(nb_reservations__gt=0)
            .order_by("-nb_reservations", "-depense_totale")[:limite])

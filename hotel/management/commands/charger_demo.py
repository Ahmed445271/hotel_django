"""
Commande : python manage.py charger_demo
Crée un compte administrateur et des données d'exemple (chambres, clients, réservations).
Ne fait rien si des chambres existent déjà : on peut la relancer sans risque.
"""
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from hotel.models import Chambre, Client, Reservation, aujourdhui

EQUIPEMENTS = {
    "simple": "WiFi, TV, Climatisation, Douche",
    "double": "WiFi, TV, Climatisation, Douche, Mini-bar",
    "suite": "WiFi, TV, Climatisation, Baignoire, Mini-bar, Balcon",
}
DESCRIPTIONS = {
    "simple": "Chambre simple confortable avec salle de bain privée.",
    "double": "Chambre double spacieuse, idéale pour deux personnes.",
    "suite": "Suite de luxe avec salon séparé et vue dégagée.",
}


class Command(BaseCommand):
    help = "Crée l'administrateur (admin / admin123) et des données de démonstration."

    def handle(self, *args, **options):
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@hotel.local", "admin123")
            self.stdout.write("Compte administrateur créé : admin / admin123")

        if Chambre.objects.exists():
            self.stdout.write("Des données existent déjà : rien à charger.")
            return

        chambres = {}
        for num, type_chambre, prix in [(101, "simple", 80), (102, "simple", 85),
                                        (103, "double", 120), (104, "double", 130),
                                        (201, "double", 140), (202, "suite", 250),
                                        (203, "suite", 280), (301, "suite", 350)]:
            chambres[num] = Chambre.objects.create(
                num_chambre=num, type_chambre=type_chambre, prix_nuit=prix,
                description=DESCRIPTIONS[type_chambre], equipements=EQUIPEMENTS[type_chambre])

        clients = [Client.objects.create(nom=n, prenom=p, telephone=t) for n, p, t in [
            ("Ben Ali", "Sami", "20123456"), ("Trabelsi", "Amel", "+21698765432"),
            ("Gharbi", "Mohamed", "55123987"), ("Jebali", "Ines", "22334455"),
            ("Mejri", "Youssef", "99887766")]]

        jour = aujourdhui()
        # (client, chambre, début, fin) en nombre de jours par rapport à aujourd'hui
        for c, ch, debut, fin in [(0, 101, -12, -9), (1, 102, -8, -5), (0, 103, -20, -17),
                                  (2, 104, -6, -3), (0, 103, -1, 2), (1, 201, 0, 3),
                                  (3, 202, -2, 1), (2, 101, 2, 5), (4, 104, 5, 9),
                                  (0, 301, 10, 14)]:
            Reservation.objects.create(client=clients[c], chambre=chambres[ch],
                                       date_debut=jour + timedelta(days=debut),
                                       date_fin=jour + timedelta(days=fin))
        self.stdout.write(self.style.SUCCESS("Données de démonstration chargées."))

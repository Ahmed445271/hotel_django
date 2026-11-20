"""Tests automatiques : python manage.py test"""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Chambre, Client, Reservation, aujourdhui
from .statistiques import calculer_statistiques


def jour(n):
    """Date d'aujourd'hui + n jours."""
    return aujourdhui() + timedelta(days=n)


class BaseTest(TestCase):
    def setUp(self):
        self.chambre = Chambre.objects.create(num_chambre=101, type_chambre="simple", prix_nuit=Decimal("80"))
        self.chambre2 = Chambre.objects.create(num_chambre=102, type_chambre="suite", prix_nuit=Decimal("200"))
        self.un_client = Client.objects.create(nom="Ben Ali", prenom="Sami", telephone="20123456")

    def reserver(self, debut, fin, chambre=None):
        return Reservation.objects.create(client=self.un_client, chambre=chambre or self.chambre,
                                          date_debut=jour(debut), date_fin=jour(fin))


class ReglesMetierTests(BaseTest):
    def test_prix_total(self):
        self.assertEqual(self.reserver(0, 3).prix_total, Decimal("240"))

    def test_chevauchement_refuse(self):
        self.reserver(0, 3)
        with self.assertRaises(ValidationError):
            Reservation(client=self.un_client, chambre=self.chambre,
                        date_debut=jour(2), date_fin=jour(5)).verifier_dates()

    def test_depart_egal_arrivee_accepte(self):
        self.reserver(0, 3)
        Reservation(client=self.un_client, chambre=self.chambre,
                    date_debut=jour(3), date_fin=jour(5)).verifier_dates()   # pas d'erreur

    def test_dates_invalides(self):
        for debut, fin in [(-2, 1), (5, 5), (6, 4)]:
            with self.assertRaises(ValidationError):
                Reservation(client=self.un_client, chambre=self.chambre,
                            date_debut=jour(debut), date_fin=jour(fin)).verifier_dates()

    def test_statut_chambre(self):
        self.assertEqual(self.chambre.statut, "libre")
        self.reserver(-1, 2)
        self.assertEqual(Chambre.objects.get(pk=self.chambre.pk).statut, "occupée")
        self.assertEqual(Chambre.objects.avec_statut().filter(occupee=True).count(), 1)

    def test_liberer_et_annuler(self):
        sejour = self.reserver(-2, 2)
        sejour.liberer()
        self.assertEqual(sejour.date_fin, jour(0))
        self.assertEqual(sejour.prix_total, Decimal("160"))        # 2 nuits réellement passées
        futur = self.reserver(5, 7)
        with self.assertRaises(ValidationError):
            futur.liberer()
        futur.annuler()
        self.assertFalse(Reservation.objects.filter(pk=futur.pk).exists())
        with self.assertRaises(ValidationError):
            self.reserver(-1, 1, self.chambre2).annuler()

    def test_statistiques(self):
        self.reserver(-1, 2)
        stats = calculer_statistiques()
        self.assertEqual((stats["total_chambres"], stats["chambres_libres"]), (2, 1))
        self.assertEqual(stats["taux_occupation"], 50.0)


class PagesTests(BaseTest):
    def test_pages_publiques(self):
        for url in (reverse("accueil"), reverse("liste_chambres"),
                    reverse("detail_chambre", args=[self.chambre.pk]),
                    reverse("liste_chambres") + "?type=suite&statut=libre"):
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_pages_personnel_protegees(self):
        for nom in ("dashboard", "gestion_chambres", "gestion_clients", "gestion_reservations"):
            reponse = self.client.get(reverse(nom))
            self.assertEqual(reponse.status_code, 302)
            self.assertIn("/connexion/", reponse.url)

    def test_pages_personnel_connecte(self):
        self.client.force_login(User.objects.create_user("emp", password="x", is_staff=True))
        self.reserver(-1, 2)
        pages = ["dashboard", "gestion_chambres", "gestion_clients", "gestion_reservations",
                 "chambre_ajouter", "client_ajouter", "reservation_ajouter"]
        for nom in pages:
            self.assertEqual(self.client.get(reverse(nom)).status_code, 200, nom)
        self.assertEqual(self.client.get(reverse("dashboard") + "?filtre=passees").status_code, 200)
        self.assertEqual(self.client.get(reverse("gestion_clients") + "?q=ben").status_code, 200)

    def test_reservation_depuis_la_page_detail(self):
        url = reverse("detail_chambre", args=[self.chambre.pk])
        donnees = {"nom": "Gharbi", "prenom": "Ali", "telephone": "55123987",
                   "date_debut": jour(1).isoformat(), "date_fin": jour(3).isoformat()}
        self.assertEqual(self.client.post(url, donnees).status_code, 302)
        self.assertEqual(Reservation.objects.count(), 1)
        reponse = self.client.post(url, donnees)          # même période : refusée
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(Reservation.objects.count(), 1)

    def test_suppression_protegee_et_liberation(self):
        self.client.force_login(User.objects.create_user("emp", password="x", is_staff=True))
        sejour = self.reserver(-1, 2)
        self.client.post(reverse("chambre_supprimer", args=[self.chambre.pk]))
        self.assertTrue(Chambre.objects.filter(pk=self.chambre.pk).exists())   # refusé
        self.client.post(reverse("reservation_liberer", args=[sejour.pk]))
        self.client.post(reverse("chambre_supprimer", args=[self.chambre.pk]))
        self.assertFalse(Chambre.objects.filter(pk=self.chambre.pk).exists())  # maintenant OK

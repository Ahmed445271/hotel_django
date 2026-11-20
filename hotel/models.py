"""
models.py : LES TABLES DE LA BASE DE DONNÉES
============================================
Avec Django, chaque classe ci-dessous devient une table SQLite.
On n'écrit PAS de SQL : Django le génère (c'est l'ORM).

    Chambre      (Num_chambre, Type, Prix_nuit, Statut)      <- énoncé
    Client       (Id_client, Nom, Prénom, Téléphone)          <- énoncé
    Reservation  (Id_res, Id_client, Num_chambre, dates)      <- énoncé

Le "Statut" (libre/occupée) n'est PAS stocké : il est CALCULÉ à partir des
réservations et de la date d'aujourd'hui. Il ne peut donc jamais être faux.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Exists, OuterRef
from django.utils import timezone


def aujourdhui():
    """Date d'aujourd'hui (fuseau Africa/Tunis)."""
    return timezone.localdate()


validateur_telephone = RegexValidator(
    r"^\+?[0-9 ]{8,16}$", "Téléphone invalide (8 chiffres minimum, ex : 20123456).")


# ----------------------------------------------------------------------
# CHAMBRE
# ----------------------------------------------------------------------
class ChambreQuerySet(models.QuerySet):
    """Requêtes personnalisées sur les chambres."""

    def avec_statut(self, jour=None):
        """Ajoute à chaque chambre l'information 'occupee' (True/False) :
        True si une réservation couvre ce jour (début <= jour < fin).
        Une seule requête SQL pour TOUTES les chambres (rapide)."""
        jour = jour or aujourdhui()
        en_cours = Reservation.objects.filter(
            chambre=OuterRef("pk"), date_debut__lte=jour, date_fin__gt=jour)
        return self.annotate(occupee=Exists(en_cours))


class Chambre(models.Model):
    TYPES = [("simple", "Simple"), ("double", "Double"), ("suite", "Suite")]

    num_chambre = models.PositiveIntegerField(
        "Numéro de chambre", unique=True, validators=[MinValueValidator(1)])
    type_chambre = models.CharField("Type", max_length=10, choices=TYPES)
    prix_nuit = models.DecimalField(
        "Prix par nuit", max_digits=8, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))])
    description = models.TextField(blank=True)
    equipements = models.CharField(
        "Équipements", max_length=200, blank=True,
        help_text="Séparés par des virgules. Ex : WiFi, TV, Climatisation")
    photo = models.FileField("Photo", upload_to="chambres/", blank=True)

    objects = ChambreQuerySet.as_manager()

    class Meta:
        ordering = ["num_chambre"]

    def __str__(self):
        return f"Chambre {self.num_chambre} ({self.get_type_chambre_display()})"

    @property
    def liste_equipements(self):
        return [e.strip() for e in self.equipements.split(",") if e.strip()]

    def reservation_actuelle(self):
        """Le séjour en cours dans cette chambre (ou None)."""
        jour = aujourdhui()
        return self.reservations.filter(date_debut__lte=jour, date_fin__gt=jour).first()

    @property
    def est_occupee(self):
        # Si la chambre vient de avec_statut(), l'information est déjà là
        if hasattr(self, "occupee"):
            return self.occupee
        return self.reservation_actuelle() is not None

    @property
    def statut(self):
        return "occupée" if self.est_occupee else "libre"


# ----------------------------------------------------------------------
# CLIENT
# ----------------------------------------------------------------------
class Client(models.Model):
    nom = models.CharField(max_length=50)
    prenom = models.CharField("Prénom", max_length=50)
    telephone = models.CharField("Téléphone", max_length=20, validators=[validateur_telephone])

    class Meta:
        ordering = ["nom", "prenom"]

    def __str__(self):
        return f"{self.nom} {self.prenom}"


# ----------------------------------------------------------------------
# RÉSERVATION
# ----------------------------------------------------------------------
class Reservation(models.Model):
    # PROTECT : on ne peut pas supprimer un client/une chambre qui a des réservations
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="reservations")
    chambre = models.ForeignKey(Chambre, on_delete=models.PROTECT, related_name="reservations")
    date_debut = models.DateField("Arrivée")
    date_fin = models.DateField("Départ")   # jour du départ : cette nuit-là n'est pas comptée
    # Copie du prix au moment de la réservation : si le prix de la chambre change
    # plus tard, les anciennes réservations gardent leur prix.
    prix_nuit = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, editable=False)
    prix_total = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_debut", "-id"]

    def __str__(self):
        return f"{self.numero} - {self.client} - chambre {self.chambre.num_chambre}"

    # ----- Propriétés d'affichage -----
    @property
    def numero(self):
        return f"RES-{self.pk:03d}"

    @property
    def nb_nuits(self):
        return (self.date_fin - self.date_debut).days

    @property
    def statut_code(self):
        jour = aujourdhui()
        if self.date_debut <= jour < self.date_fin:
            return "en_cours"
        if self.date_debut > jour:
            return "a_venir"
        return "terminee"

    @property
    def statut(self):
        return {"en_cours": "En cours", "a_venir": "À venir", "terminee": "Terminée"}[self.statut_code]

    # ----- Règles métier -----
    def verifier_dates(self):
        """Vérifie les dates. Lève ValidationError (message affiché à l'utilisateur)."""
        if self.date_debut is None or self.date_fin is None or self.chambre_id is None:
            return   # les erreurs de champ manquant sont déjà signalées par le formulaire
        if self.date_fin <= self.date_debut:
            raise ValidationError("La date de fin doit être après la date de début.")
        if self._state.adding and self.date_debut < aujourdhui():
            raise ValidationError("La date de début ne peut pas être dans le passé.")
        # Deux périodes se chevauchent si : nouveau_début < ancienne_fin ET nouvelle_fin > ancien_début
        chevauchement = Reservation.objects.filter(
            chambre_id=self.chambre_id,
            date_debut__lt=self.date_fin,
            date_fin__gt=self.date_debut,
        ).exclude(pk=self.pk)
        if chevauchement.exists():
            raise ValidationError(
                f"La chambre {self.chambre.num_chambre} est déjà réservée sur cette période.")

    def clean(self):
        """Appelée automatiquement par les formulaires."""
        self.verifier_dates()

    def save(self, *args, **kwargs):
        if self.prix_nuit is None:                  # première sauvegarde
            self.prix_nuit = self.chambre.prix_nuit
        self.prix_total = self.nb_nuits * self.prix_nuit
        super().save(*args, **kwargs)

    def liberer(self):
        """Libère la chambre (départ anticipé du client).
        - séjour commencé : la date de fin devient aujourd'hui
        - séjour qui commence aujourd'hui : la réservation est supprimée"""
        jour = aujourdhui()
        if not (self.date_debut <= jour < self.date_fin):
            raise ValidationError("Ce séjour n'est pas en cours.")
        if self.date_debut == jour:
            self.delete()
        else:
            self.date_fin = jour
            self.save()

    def annuler(self):
        """Annule une réservation À VENIR."""
        if self.date_debut <= aujourdhui():
            raise ValidationError("Séjour déjà commencé : utilisez « Libérer la chambre ».")
        self.delete()

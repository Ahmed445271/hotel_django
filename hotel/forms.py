"""
forms.py : LES FORMULAIRES
Un ModelForm crée automatiquement un formulaire à partir d'un modèle
et applique ses règles de validation.
"""
from django import forms

from .models import Chambre, Client, Reservation, aujourdhui, validateur_telephone


class DateHtml(forms.DateInput):
    """Champ date avec le sélecteur de calendrier du navigateur."""
    input_type = "date"

    def __init__(self, **kwargs):
        kwargs.setdefault("format", "%Y-%m-%d")
        super().__init__(**kwargs)


class ChambreForm(forms.ModelForm):
    class Meta:
        model = Chambre
        fields = ["num_chambre", "type_chambre", "prix_nuit", "description", "equipements", "photo"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["nom", "prenom", "telephone"]


class ReservationForm(forms.ModelForm):
    """Formulaire du personnel : on choisit un client existant et une chambre."""
    class Meta:
        model = Reservation
        fields = ["client", "chambre", "date_debut", "date_fin"]
        widgets = {"date_debut": DateHtml(), "date_fin": DateHtml()}


class ReservationRapideForm(forms.Form):
    """Formulaire de la page 'détails d'une chambre' : le visiteur donne ses
    coordonnées et ses dates. Le client est créé automatiquement s'il n'existe pas."""
    nom = forms.CharField(max_length=50)
    prenom = forms.CharField(label="Prénom", max_length=50)
    telephone = forms.CharField(label="Téléphone", max_length=20, validators=[validateur_telephone])
    date_debut = forms.DateField(label="Arrivée", widget=DateHtml())
    date_fin = forms.DateField(label="Départ", widget=DateHtml())

    def __init__(self, *args, chambre, **kwargs):
        super().__init__(*args, **kwargs)
        self.chambre = chambre
        self.fields["date_debut"].initial = aujourdhui()

    def clean(self):
        donnees = super().clean()
        # On réutilise EXACTEMENT les mêmes règles que le personnel (chevauchement, etc.)
        Reservation(chambre=self.chambre, date_debut=donnees.get("date_debut"),
                    date_fin=donnees.get("date_fin")).verifier_dates()
        return donnees

    def enregistrer(self):
        d = self.cleaned_data
        client, _ = Client.objects.get_or_create(
            telephone=d["telephone"], defaults={"nom": d["nom"], "prenom": d["prenom"]})
        return Reservation.objects.create(
            client=client, chambre=self.chambre, date_debut=d["date_debut"], date_fin=d["date_fin"])

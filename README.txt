HOTEL - Projet 1 Python (Django + SQLite)

LANCER (dans le terminal VS Code, dossier hotel_django) :
    pip install -r requirements.txt
    python manage.py migrate
    python manage.py charger_demo
    python manage.py runserver
Puis ouvrir Edge sur  http://127.0.0.1:8000/
(Windows : ou double-cliquer sur lancer.bat qui fait tout et ouvre Edge)

COMPTE ADMINISTRATEUR (demo) : admin / admin123   -> a changer pour un vrai usage
PAGES : /  /chambres/  /chambres/<id>/  /connexion/  /tableau-de-bord/  /gestion/chambres/
        /gestion/clients/  /gestion/reservations/  /admin/ (interface Django)
TESTS : python manage.py test
REPARTIR DE ZERO : supprimer db.sqlite3 puis refaire migrate + charger_demo

FICHIERS : hotel/models.py (tables) | hotel/views.py (pages) | hotel/urls.py (adresses)
           hotel/forms.py (formulaires) | hotel/statistiques.py | hotel/templates/ (HTML)
           hotel/static/hotel/style.css (design) | config/settings.py (reglages)

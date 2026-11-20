@echo off
REM Double-cliquez sur ce fichier pour lancer le site (Windows).
cd /d %~dp0
echo === Installation de Django (une seule fois) ===
python -m pip install -r requirements.txt
echo === Preparation de la base de donnees ===
python manage.py migrate
python manage.py charger_demo
echo === Ouverture dans Edge ===
start msedge http://127.0.0.1:8000/
echo Le site tourne. Pour l'arreter : fermez cette fenetre (ou Ctrl+C).
python manage.py runserver
pause

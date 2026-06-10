#!/usr/bin/env bash
# Lance le serveur de développement OptiLinéaire
set -e
cd "$(dirname "$0")"

# Créer le venv si absent
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate

pip install -r requirements.txt --quiet

python manage.py migrate

python manage.py runserver

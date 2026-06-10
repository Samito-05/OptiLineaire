# Lance le serveur de développement OptiLinéaire
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# Créer le venv si absent
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

& ".venv\Scripts\Activate.ps1"

pip install -r requirements.txt --quiet

python manage.py migrate

python manage.py runserver

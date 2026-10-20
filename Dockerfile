FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_DEBUG=0

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY manage.py ./
COPY OptiLineaire ./OptiLineaire
COPY pb_lineaire ./pb_lineaire

# collectstatic n'a besoin que d'une clé factice ; la vraie vient de l'environnement
RUN DJANGO_SECRET_KEY=build-placeholder python manage.py collectstatic --no-input

# Rien n'est écrit sur le disque : pas de base, pas de sessions
RUN useradd --create-home app
USER app

EXPOSE 8000

# Les calculs sont bornés (nœuds, coupes, temps) : 30 s couvrent largement le pire cas
CMD ["gunicorn", "OptiLineaire.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--timeout", "30", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]

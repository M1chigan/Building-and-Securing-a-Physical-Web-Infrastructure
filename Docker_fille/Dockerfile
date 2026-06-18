FROM python:3.11-slim

# Installation des dépendances système nécessaires (comme curl pour le healthcheck)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

COPY . .

EXPOSE 5000

# Lancement avec Gunicorn (4 processus de production en tâche de fond)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "Dashboard:app"]

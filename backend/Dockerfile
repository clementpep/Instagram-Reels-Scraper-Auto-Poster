# Utilise Python 3.11 slim pour un container plus léger
FROM python:3.11-slim

# Définit le répertoire de travail
WORKDIR /app

# Installe les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copie les fichiers de dépendances
COPY backend/requirements.txt .

# Installe les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copie le code source backend
COPY backend/ ./backend/

# Crée les dossiers nécessaires
RUN mkdir -p database downloads logs

# Copie les scripts d'initialisation
COPY *.py ./

# Configure les variables d'environnement
ENV PYTHONPATH=/app
ENV FLASK_APP=backend.src.api
ENV FLASK_ENV=production
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Port exposed
EXPOSE 5000

# Startup script
COPY backend/docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Default commande
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "-m", "backend.src.app"]
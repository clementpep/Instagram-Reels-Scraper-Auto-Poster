#!/bin/bash
set -e

echo "🐳 Starting ReelsAutoPilot Backend Container..."

# Attendre que les dossiers soient montés
echo "📁 Checking required directories..."
mkdir -p /app/database /app/downloads /app/logs

# Initialiser la configuration si nécessaire
echo "⚙️ Initializing configuration..."
if [ ! -f "/app/database/sqlite.db" ]; then
    echo "🗄️ Database not found, initializing..."
    python -m backend.src.init_config
fi

# Vérifier la connectivité (optionnel)
echo "🔍 Checking system health..."

# Démarrer l'application selon le mode
if [ "$1" = "app" ]; then
    echo "🚀 Starting main application..."
    exec python -m backend.src.app
elif [ "$1" = "api" ]; then
    echo "🌐 Starting API server only..."
    exec python -m backend.src.api
elif [ "$1" = "dashboard" ]; then
    echo "📊 Starting dashboard..."
    exec python -m backend.src.dashboard
elif [ "$1" = "debug" ]; then
    echo "🐛 Starting in debug mode..."
    exec python -m backend.src.debug_app
else
    echo "🎯 Starting with custom command: $@"
    exec "$@"
fi
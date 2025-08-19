#!/bin/bash

# =================================================================
# REELS AUTOPILOT - DOCKER MANAGER
# =================================================================
# Script pour gérer facilement l'application dockerisée

set -e

# Couleurs pour les logs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonctions utilitaires
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Fonction d'aide
show_help() {
    echo "ReelsAutoPilot Docker Manager"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup     Première installation et configuration"
    echo "  build     Build les images Docker"
    echo "  start     Démarre les containers"
    echo "  stop      Arrête les containers"
    echo "  restart   Redémarre les containers"
    echo "  logs      Affiche les logs"
    echo "  status    Affiche le statut des containers"
    echo "  clean     Nettoie les images et containers"
    echo "  dev       Démarre en mode développement"
    echo "  prod      Démarre en mode production avec Nginx"
    echo "  backup    Sauvegarde la base de données"
    echo "  restore   Restaure la base de données"
    echo ""
}

# Configuration initiale
setup() {
    log_info "🚀 Configuration initiale de ReelsAutoPilot..."
    
    # Vérifier Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker n'est pas installé!"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose n'est pas installé!"
        exit 1
    fi
    
    # Créer le fichier .env s'il n'existe pas
    if [ ! -f .env ]; then
        log_info "📝 Création du fichier .env..."
        cp .env.template .env
        log_warning "⚠️  Veuillez configurer le fichier .env avant de continuer!"
        echo "   - USERNAME: Votre nom d'utilisateur Instagram"
        echo "   - PASSWORD: Votre mot de passe Instagram"
        echo "   - YOUTUBE_API_KEY: Votre clé API YouTube"
        exit 1
    fi
    
    # Créer les dossiers nécessaires
    log_info "📁 Création des dossiers..."
    mkdir -p database downloads logs nginx/ssl
    
    # Build initial
    build
    
    log_success "✅ Configuration terminée!"
    log_info "Vous pouvez maintenant utiliser: $0 start"
}

# Build des images
build() {
    log_info "🔨 Building Docker images..."
    docker-compose build --no-cache
    log_success "✅ Images construites avec succès!"
}

# Démarrer les containers
start() {
    log_info "🚀 Démarrage des containers..."
    docker-compose up -d
    
    # Attendre que les services soient prêts
    log_info "⏳ Attente que les services soient prêts..."
    sleep 10
    
    # Vérifier le statut
    if docker-compose ps | grep -q "Up"; then
        log_success "✅ Application démarrée!"
        echo ""
        echo "🌐 Frontend: http://localhost:3000"
        echo "🔌 API: http://localhost:5000"
        echo "📊 Health: http://localhost:5000/api/health"
    else
        log_error "❌ Erreur lors du démarrage"
        docker-compose logs
    fi
}

# Arrêter les containers
stop() {
    log_info "🛑 Arrêt des containers..."
    docker-compose down
    log_success "✅ Containers arrêtés!"
}

# Redémarrer
restart() {
    log_info "🔄 Redémarrage..."
    stop
    start
}

# Afficher les logs
logs() {
    if [ -n "$2" ]; then
        # Logs d'un service spécifique
        docker-compose logs -f "$2"
    else
        # Tous les logs
        docker-compose logs -f
    fi
}

# Statut des containers
status() {
    log_info "📊 Statut des containers:"
    docker-compose ps
    
    echo ""
    log_info "💾 Utilisation des volumes:"
    docker volume ls | grep reels-autopilot || echo "Aucun volume trouvé"
    
    echo ""
    log_info "🔗 URLs disponibles:"
    echo "   Frontend: http://localhost:3000"
    echo "   API: http://localhost:5000"
    echo "   Health: http://localhost:5000/api/health"
}

# Nettoyage
clean() {
    log_warning "🧹 Nettoyage des images et containers..."
    read -p "Êtes-vous sûr? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v
        docker-compose rm -f
        docker system prune -f
        log_success "✅ Nettoyage terminé!"
    else
        log_info "Nettoyage annulé."
    fi
}

# Mode développement
dev() {
    log_info "🔧 Démarrage en mode développement..."
    docker-compose -f docker-compose.yml up --build
}

# Mode production
prod() {
    log_info "🏭 Démarrage en mode production..."
    docker-compose --profile production up -d --build
    log_success "✅ Mode production démarré avec Nginx!"
    echo "🌐 Application: http://localhost"
}

# Sauvegarde
backup() {
    log_info "💾 Sauvegarde de la base de données..."
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).db"
    docker-compose exec backend cp /app/database/sqlite.db "/app/database/$BACKUP_FILE"
    log_success "✅ Sauvegarde créée: database/$BACKUP_FILE"
}

# Restauration
restore() {
    if [ -z "$2" ]; then
        log_error "Usage: $0 restore <backup_file>"
        exit 1
    fi
    
    log_info "📥 Restauration de la base de données..."
    docker-compose exec backend cp "/app/database/$2" /app/database/sqlite.db
    restart
    log_success "✅ Base de données restaurée!"
}

# Main
case $1 in
    setup)
        setup
        ;;
    build)
        build
        ;;
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    logs)
        logs "$@"
        ;;
    status)
        status
        ;;
    clean)
        clean
        ;;
    dev)
        dev
        ;;
    prod)
        prod
        ;;
    backup)
        backup
        ;;
    restore)
        restore "$@"
        ;;
    *)
        show_help
        ;;
esac
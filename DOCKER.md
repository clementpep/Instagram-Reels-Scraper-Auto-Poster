# ReelsAutoPilot - Déploiement Docker 🐳

Guide complet pour déployer ReelsAutoPilot avec Docker et Docker Compose.

## 🎯 Vue d'ensemble

L'application est composée de 3 services principaux :
- **Backend** : API Python/Flask (port 5000)
- **Frontend** : Interface React (port 3000) 
- **Nginx** : Reverse proxy (port 80) - optionnel pour la production

## 📋 Prérequis

- Docker >= 20.10
- Docker Compose >= 2.0
- 2GB RAM minimum
- 5GB espace disque

## 🚀 Installation rapide

### 1. Configuration initiale

```bash
# Cloner le repository
git clone <votre-repo>
cd reels-autopilot

# Rendre le script exécutable
chmod +x docker-manager.sh

# Configuration initiale
./docker-manager.sh setup
```

### 2. Configurer les variables d'environnement

Editez le fichier `.env` créé automatiquement :

```bash
# Instagram Configuration
USERNAME=votre_username_instagram
PASSWORD=votre_password_instagram

# YouTube Configuration  
YOUTUBE_API_KEY=votre_cle_api_youtube

# Frontend Configuration
REACT_APP_API_URL=http://localhost:5000
```

### 3. Démarrer l'application

```bash
# Mode développement
./docker-manager.sh start

# Ou mode production avec Nginx
./docker-manager.sh prod
```

## 🛠 Commandes disponibles

```bash
# Configuration et build
./docker-manager.sh setup     # Première installation
./docker-manager.sh build     # Rebuild des images

# Gestion des containers
./docker-manager.sh start     # Démarrer
./docker-manager.sh stop      # Arrêter
./docker-manager.sh restart   # Redémarrer
./docker-manager.sh status    # Statut

# Debugging et monitoring
./docker-manager.sh logs      # Tous les logs
./docker-manager.sh logs backend  # Logs d'un service
./docker-manager.sh logs frontend

# Modes spéciaux
./docker-manager.sh dev       # Mode développement (logs visibles)
./docker-manager.sh prod      # Mode production avec Nginx

# Maintenance
./docker-manager.sh backup    # Sauvegarder la DB
./docker-manager.sh restore backup_20250819_120000.db
./docker-manager.sh clean     # Nettoyer
```

## 🌐 URLs d'accès

Après démarrage :
- **Frontend** : http://localhost:3000
- **API** : http://localhost:5000  
- **Health Check** : http://localhost:5000/api/health
- **Production (avec Nginx)** : http://localhost

## 📁 Structure des volumes

Les données persistantes sont stockées dans :

```
./database/     # Base de données SQLite
./downloads/    # Vidéos téléchargées
./logs/         # Logs de l'application
```

## 🔧 Modes de déploiement

### Mode Développement
```bash
./docker-manager.sh dev
```
- Logs visibles en temps réel
- Hot reload activé
- Debug mode

### Mode Production
```bash
./docker-manager.sh prod
```
- Nginx reverse proxy
- Optimisations performance
- SSL ready (avec certificats)

## 📊 Monitoring et maintenance

### Vérifier la santé de l'application
```bash
curl http://localhost:5000/api/health
```

### Consulter les logs
```bash
# Logs en temps réel
./docker-manager.sh logs

# Logs d'un service spécifique
./docker-manager.sh logs backend
./docker-manager.sh logs frontend
./docker-manager.sh logs nginx
```

### Sauvegarde automatique
```bash
# Créer une sauvegarde
./docker-manager.sh backup

# Restaurer une sauvegarde
./docker-manager.sh restore backup_20250819_120000.db
```

## 🚨 Dépannage

### L'application ne démarre pas
```bash
# Vérifier les logs
./docker-manager.sh logs

# Rebuild complet
./docker-manager.sh stop
./docker-manager.sh build
./docker-manager.sh start
```

### Erreurs de connexion API
1. Vérifier que le backend est démarré : `./docker-manager.sh status`
2. Tester l'API : `curl http://localhost:5000/api/health`
3. Vérifier les logs backend : `./docker-manager.sh logs backend`

### Base de données corrompue
```bash
# Restaurer une sauvegarde
./docker-manager.sh restore <fichier_backup>

# Ou réinitialiser (ATTENTION: perte de données)
rm database/sqlite.db
./docker-manager.sh restart
```

### Problèmes de permissions
```bash
# Donner les bonnes permissions
sudo chown -R $USER:$USER database downloads logs
chmod 755 database downloads logs
```

## 🔒 Sécurité

### Pour la production
1. **Changer les variables sensibles** dans `.env`
2. **Configurer HTTPS** avec des certificats SSL
3. **Limiter l'accès réseau** aux ports nécessaires
4. **Configurer un firewall** approprié

### Variables d'environnement sensibles
Ne jamais committer le fichier `.env` avec des credentials réels !

## 🚀 Déploiement en production

### Sur un VPS/Serveur dédié
```bash
# Cloner et configurer
git clone <repo> && cd reels-autopilot
./docker-manager.sh setup

# Configurer .env avec les vraies valeurs
vim .env

# Démarrer en mode production
./docker-manager.sh prod
```

### Avec un nom de domaine
1. Pointer le domaine vers votre serveur
2. Configurer SSL dans `nginx/nginx.conf`
3. Ajuster `REACT_APP_API_URL` dans `.env`

## 📈 Optimisations

### Pour de gros volumes
- Augmenter `client_max_body_size` dans Nginx
- Ajuster les timeouts
- Considérer PostgreSQL au lieu de SQLite

### Pour la performance
- Activer la compression Gzip ✅
- Cache des assets statiques ✅  
- Rate limiting ✅
- Load balancing (si multiple instances)

## 🆘 Support

En cas de problème :
1. Consulter les logs : `./docker-manager.sh logs`
2. Vérifier la configuration : `./docker-manager.sh status`
3. Redémarrer : `./docker-manager.sh restart`
4. Rebuild si nécessaire : `./docker-manager.sh build`
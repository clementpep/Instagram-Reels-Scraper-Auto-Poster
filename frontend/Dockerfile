# Stage 1: Build de l'application React
FROM node:18-alpine AS builder

# Définit le répertoire de travail
WORKDIR /app

# Copie les fichiers de dépendances
COPY package*.json ./

# Installe les dépendances
RUN npm ci

# Copie le code source
COPY . .

# Arguments de build pour la configuration
ARG REACT_APP_API_URL=http://localhost:5000
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# Build l'application pour la production
RUN npm run build

# Stage 2: Serveur Nginx pour servir l'application
FROM nginx:alpine

# Copie la configuration Nginx personnalisée
COPY nginx.conf /etc/nginx/nginx.conf

# Copie les fichiers buildés depuis le stage précédent
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose le port 80
EXPOSE 80

# Commande de démarrage
CMD ["nginx", "-g", "daemon off;"]
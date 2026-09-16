# Étape 1 : Build frontend
FROM node:20 AS build
WORKDIR /app

# Environnement d'affichage (DEV/PROD) : injecté au build Vite via variables `VITE_*`
ARG VITE_DEPLOY_ENV=dev
ARG VITE_ENV_LABEL=
ENV VITE_DEPLOY_ENV=$VITE_DEPLOY_ENV
ENV VITE_ENV_LABEL=$VITE_ENV_LABEL

# Copier uniquement package.json + lock
COPY package*.json ./

# Installer les dépendances (déterministe) + fixer les mismatches esbuild
# observés en build Docker (host JS vs binaire natif).
RUN npm ci \
  && npm i --no-save esbuild@0.27.4 @esbuild/linux-x64@0.27.4 \
  && npm rebuild esbuild

# Copier le reste du projet
COPY . .

# Build
RUN npm run build

# Étape 2 : Serveur statique Nginx (+ proxy /api → backend compose service `backend`)
FROM nginx:1.25
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html



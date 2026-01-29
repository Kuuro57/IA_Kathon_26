FROM node:20-slim

WORKDIR /app

# On copie d'abord les fichiers de configuration pour optimiser le cache Docker
COPY WebInterface/package*.json ./

RUN npm install

# On copie le reste du contenu du dossier WebInterface
COPY WebInterface/ .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
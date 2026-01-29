FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code
COPY . .

# Exposition du port FastAPI
EXPOSE 8001

# Commande pour lancer l'app avec rechargement automatique (mode dev)
CMD ["python", "-c", "from app_bd import mine_data; mine_data()"]
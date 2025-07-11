#!/bin/bash

# Dental AI Startup Script
echo "🦷 Démarrage de Dental AI..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Fichier .env manquant!"
    echo "Créez un fichier .env avec votre clé API OpenAI:"
    echo "OPENAI_API_KEY=your_openai_api_key_here"
    exit 1
fi

# Check if requirements are installed
echo "📦 Vérification des dépendances..."
python3 -c "import flask, openai" 2>/dev/null || {
    echo "📦 Installation des dépendances..."
    pip3 install -r requirements.txt
}

# Check if DATA directory exists
if [ ! -d "DATA/TRAITEMENTS_JSON" ]; then
    echo "⚠️  Répertoire DATA/TRAITEMENTS_JSON introuvable!"
    echo "Assurez-vous que vos données de traitement sont dans le bon répertoire."
fi

# Start the application
echo "🚀 Lancement de l'application..."
echo "📱 Interface accessible sur: http://localhost:5001"
echo "🔧 Mode debug activé pour le développement"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter l'application"
echo ""

python3 app.py 
#!/bin/bash
# -*- coding: utf-8 -*-
# Script de démarrage complet pour le chatbot Goo-net Pit

echo "🚗 Démarrage du système Goo-net Pit Chatbot"
echo "============================================="

# Vérification des dépendances Python
echo "📦 Vérification des dépendances..."
python3 -c "import fastapi, uvicorn, boto3, faiss, sentence_transformers" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Dépendances manquantes. Installation..."
    pip install fastapi uvicorn boto3 faiss-cpu sentence-transformers pydantic
fi

# Création des répertoires nécessaires
echo "📁 Création des répertoires..."
mkdir -p /workspaces/SmarBot/data/logs
mkdir -p /workspaces/SmarBot/data/json
mkdir -p /workspaces/SmarBot/data/faiss_index

# Génération des données JSON (si pas déjà fait)
echo "🔄 Préparation des données..."
cd /workspaces/SmarBot
if [ ! -f "data/json/diagnostic_articles.json" ]; then
    echo "   Conversion CSV vers JSON..."
    python backend/api/data_processing/csv_converter.py
fi

# Génération de l'index FAISS (si pas déjà fait)
if [ ! -f "data/faiss_index/articles.index" ]; then
    echo "   Création de l'index de recherche vectorielle..."
    python backend/api/data_processing/vector_search.py
fi

# Fonction pour arrêter les processus en cours
cleanup() {
    echo "🛑 Arrêt des services..."
    pkill -f "uvicorn.*goonet_api"
    pkill -f "python.*http.server.*3000"
    exit 0
}

# Trap pour le nettoyage en cas d'interruption
trap cleanup SIGINT SIGTERM

# Démarrage de l'API Backend
echo "🚀 Démarrage de l'API Backend (port 8001)..."
cd /workspaces/SmarBot/backend/api
uvicorn goonet_api:app --host 0.0.0.0 --port 8001 --reload &
API_PID=$!

# Attendre que l'API soit prête
echo "⏳ Attente de l'initialisation de l'API..."
for i in {1..30}; do
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "✅ API Backend prête!"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo "❌ Timeout - L'API n'a pas démarré"
        cleanup
    fi
done

# Démarrage du serveur Frontend
echo "🌐 Démarrage du serveur Frontend (port 3000)..."
cd /workspaces/SmarBot/frontend
python3 -m http.server 3000 &
FRONTEND_PID=$!

# Attendre que le frontend soit prêt
sleep 2
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend prêt!"
else
    echo "❌ Erreur de démarrage du frontend"
    cleanup
fi

echo ""
echo "🎉 Système Goo-net Pit Chatbot démarré avec succès!"
echo "======================================================"
echo ""
echo "🔗 URLs disponibles:"
echo "   💬 Interface Chat:        http://localhost:3000/goonet-chat.html"
echo "   📚 Documentation API:     http://localhost:8001/docs"
echo "   🏥 État de santé API:     http://localhost:8001/health"
echo "   📊 Statistiques:          http://localhost:8001/stats"
echo ""
echo "🛠️ Fonctionnalités:"
echo "   ✅ Chat intelligent en japonais"
echo "   ✅ Recherche vectorielle dans 5 articles de diagnostic"
echo "   ✅ Extraction d'entités (marque, modèle, année, codes OBD)"
echo "   ✅ Recommandations de garages"
echo "   ✅ Formulaires de prise de rendez-vous pré-remplis"
echo "   ✅ Journalisation des conversations"
echo "   ✅ Système de feedback"
echo ""
echo "🚨 Configuration AWS Bedrock:"
echo "   Pour utiliser Claude Sonnet 3.5:"
echo "   export USE_AWS_BEDROCK=true"
echo "   export AWS_ACCESS_KEY_ID=your_key"
echo "   export AWS_SECRET_ACCESS_KEY=your_secret"
echo "   export AWS_DEFAULT_REGION=us-east-1"
echo ""
echo "📖 Tests rapides:"
echo "   curl -X POST http://localhost:8001/chat -H 'Content-Type: application/json' -d '{\"message\":\"ホンダのN-BOXでハンドルが重い\"}'"
echo ""
echo "Appuyez sur Ctrl+C pour arrêter tous les services."

# Affichage des logs en temps réel
echo ""
echo "📋 Logs de l'API:"
echo "=================="

# Attendre jusqu'à interruption
wait $API_PID

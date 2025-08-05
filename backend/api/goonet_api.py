#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API FastAPI pour le chatbot Goo-net Pit
Intègre la recherche vectorielle et le moteur conversationnel
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import uuid
from datetime import datetime
import json
import os
import sys

# Ajout du chemin pour les imports
sys.path.append('/workspaces/SmarBot/backend/api/data_processing')

from chat_engine import GoonetChatEngine, ChatResponse
from vector_search import GoonetVectorSearch

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Modèles Pydantic pour l'API
class ChatMessage(BaseModel):
    message: str = Field(..., description="Message de l'utilisateur")
    session_id: Optional[str] = Field(None, description="ID de session pour le suivi")
    user_info: Optional[Dict[str, Any]] = Field(None, description="Informations utilisateur optionnelles")

class ChatResponseModel(BaseModel):
    response_id: str
    session_id: str
    message: str
    confidence: float
    sources: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    appointment_form: Optional[Dict[str, Any]] = None
    follow_up_questions: Optional[List[str]] = None
    timestamp: datetime

class SearchRequest(BaseModel):
    query: str = Field(..., description="Requête de recherche")
    max_results: int = Field(5, ge=1, le=20, description="Nombre maximum de résultats")
    min_similarity: float = Field(0.3, ge=0.0, le=1.0, description="Seuil de similarité minimum")

class FeedbackRequest(BaseModel):
    response_id: str = Field(..., description="ID de la réponse")
    rating: int = Field(..., ge=1, le=5, description="Note de 1 à 5")
    comment: Optional[str] = Field(None, description="Commentaire optionnel")

# Initialisation de l'application FastAPI
app = FastAPI(
    title="Goo-net Pit Chatbot API",
    description="API intelligente pour le diagnostic automobile et la recommandation de garages",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS pour le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Frontend React/Vite
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variables globales pour le cache des moteurs
chat_engine: Optional[GoonetChatEngine] = None
search_engine: Optional[GoonetVectorSearch] = None
conversation_logs: Dict[str, List] = {}

@app.on_event("startup")
async def startup_event():
    """Initialisation au démarrage de l'API"""
    global chat_engine, search_engine
    
    logger.info("🚀 Initialisation de l'API Goo-net Pit...")
    
    try:
        # Initialisation du moteur de chat
        use_bedrock = os.getenv('USE_AWS_BEDROCK', 'false').lower() == 'true'
        chat_engine = GoonetChatEngine(use_bedrock=use_bedrock)
        search_engine = chat_engine.search_engine
        
        logger.info(f"✅ Moteurs initialisés (Bedrock: {use_bedrock})")
        
    except Exception as e:
        logger.error(f"❌ Erreur d'initialisation: {e}")
        raise e

@app.get("/")
async def root():
    """Point d'entrée racine de l'API"""
    return {
        "service": "Goo-net Pit Chatbot API",
        "version": "1.0.0",
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "chat": "/chat",
            "search": "/search",
            "feedback": "/feedback",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Vérification de l'état de santé de l'API"""
    global chat_engine, search_engine
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "chat_engine": chat_engine is not None,
            "search_engine": search_engine is not None,
            "vector_index": search_engine.index is not None if search_engine else False
        }
    }
    
    # Vérification additionnelle
    if search_engine and search_engine.index:
        health_status["index_size"] = search_engine.index.ntotal
        health_status["metadata_count"] = len(search_engine.metadata)
    
    return health_status

@app.post("/chat", response_model=ChatResponseModel)
async def chat_endpoint(request: ChatMessage, background_tasks: BackgroundTasks):
    """Point d'entrée principal pour le chat"""
    global chat_engine
    
    if not chat_engine:
        raise HTTPException(status_code=503, detail="Moteur de chat non initialisé")
    
    # Génération des IDs
    response_id = str(uuid.uuid4())
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        # Traitement du message
        response = chat_engine.process_message(request.message)
        
        # Formatage de la réponse
        api_response = ChatResponseModel(
            response_id=response_id,
            session_id=session_id,
            message=response.message,
            confidence=response.confidence,
            sources=response.sources,
            recommendations=response.recommendations,
            appointment_form=response.appointment_form,
            follow_up_questions=response.follow_up_questions,
            timestamp=datetime.now()
        )
        
        # Logging en arrière-plan
        background_tasks.add_task(
            log_conversation,
            session_id,
            request.message,
            api_response.dict(),
            request.user_info
        )
        
        return api_response
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement du chat: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur de traitement: {str(e)}")

@app.post("/search")
async def search_endpoint(request: SearchRequest):
    """Recherche directe dans la base de connaissances"""
    global search_engine
    
    if not search_engine:
        raise HTTPException(status_code=503, detail="Moteur de recherche non initialisé")
    
    try:
        results = search_engine.search(
            query=request.query,
            k=request.max_results,
            min_similarity=request.min_similarity
        )
        
        return {
            "query": request.query,
            "results_count": len(results),
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la recherche: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur de recherche: {str(e)}")

@app.post("/feedback")
async def feedback_endpoint(request: FeedbackRequest, background_tasks: BackgroundTasks):
    """Collecte du feedback utilisateur"""
    
    # Validation du feedback
    if request.rating < 1 or request.rating > 5:
        raise HTTPException(status_code=400, detail="La note doit être entre 1 et 5")
    
    feedback_data = {
        "response_id": request.response_id,
        "rating": request.rating,
        "comment": request.comment,
        "timestamp": datetime.now().isoformat()
    }
    
    # Sauvegarde en arrière-plan
    background_tasks.add_task(save_feedback, feedback_data)
    
    return {
        "message": "Feedback enregistré avec succès",
        "feedback_id": str(uuid.uuid4())
    }

@app.get("/garages")
async def get_garages(
    location: Optional[str] = None,
    manufacturer: Optional[str] = None,
    service: Optional[str] = None
):
    """Récupération des garages avec filtres"""
    global search_engine
    
    if not search_engine:
        raise HTTPException(status_code=503, detail="Moteur de recherche non initialisé")
    
    try:
        garages = search_engine.find_nearby_garages(
            location=location,
            vehicle_manufacturer=manufacturer,
            service_type=service
        )
        
        return {
            "filters": {
                "location": location,
                "manufacturer": manufacturer,
                "service": service
            },
            "garages_count": len(garages),
            "garages": garages,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des garages: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Statistiques de l'API"""
    global search_engine, conversation_logs
    
    stats = {
        "api_version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "total_conversations": len(conversation_logs),
        "database_stats": {}
    }
    
    if search_engine:
        stats["database_stats"] = {
            "total_articles": len(search_engine.articles),
            "total_garages": len(search_engine.garages),
            "vector_index_size": search_engine.index.ntotal if search_engine.index else 0
        }
    
    return stats

# Fonctions utilitaires pour les tâches en arrière-plan
async def log_conversation(session_id: str, user_message: str, response: Dict, user_info: Optional[Dict]):
    """Journalisation des conversations"""
    global conversation_logs
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": session_id,
        "user_message": user_message,
        "response": response,
        "user_info": user_info
    }
    
    if session_id not in conversation_logs:
        conversation_logs[session_id] = []
    
    conversation_logs[session_id].append(log_entry)
    
    # Optionnel : Sauvegarde sur disque
    try:
        log_file = f"/workspaces/SmarBot/data/logs/conversation_{session_id}.json"
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(conversation_logs[session_id], f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du log: {e}")

async def save_feedback(feedback_data: Dict):
    """Sauvegarde du feedback"""
    try:
        feedback_file = "/workspaces/SmarBot/data/logs/feedback.jsonl"
        os.makedirs(os.path.dirname(feedback_file), exist_ok=True)
        
        with open(feedback_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(feedback_data, ensure_ascii=False) + '\n')
            
        logger.info(f"Feedback sauvegardé: {feedback_data['response_id']}")
        
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du feedback: {e}")

# Point d'entrée pour exécuter l'API
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "goonet_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

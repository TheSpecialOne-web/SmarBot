#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Système de recherche vectorielle pour le chatbot Goo-net Pit
Utilise FAISS pour la recherche sémantique et AWS Bedrock pour les embeddings
"""

import json
import numpy as np
import faiss
import boto3
from typing import Dict, List, Any, Optional, Tuple
import logging
from pathlib import Path
import pickle
from sentence_transformers import SentenceTransformer
import os

logger = logging.getLogger(__name__)

class GoonetVectorSearch:
    """Moteur de recherche vectorielle pour les données Goo-net Pit"""
    
    def __init__(self, 
                 use_bedrock: bool = True,
                 model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        self.use_bedrock = use_bedrock
        self.model_name = model_name
        self.embedding_dimension = 384  # Dimension pour le modèle MiniLM
        
        # Initialisation des clients
        if use_bedrock:
            try:
                self.bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
                logger.info("Client AWS Bedrock initialisé")
            except Exception as e:
                logger.warning(f"Impossible d'initialiser Bedrock, utilisation du modèle local: {e}")
                self.use_bedrock = False
        
        if not self.use_bedrock:
            self.embedding_model = SentenceTransformer(model_name)
            self.embedding_dimension = self.embedding_model.get_sentence_embedding_dimension()
            logger.info(f"Modèle d'embedding local chargé: {model_name}")
        
        # Index FAISS et métadonnées
        self.index = None
        self.metadata = []
        self.articles = []
        self.garages = []
    
    def get_embedding_bedrock(self, text: str) -> np.ndarray:
        """Obtient un embedding via AWS Bedrock (Titan Embeddings)"""
        try:
            body = json.dumps({
                "inputText": text
            })
            
            response = self.bedrock_client.invoke_model(
                modelId="amazon.titan-embed-text-v1",
                body=body,
                contentType="application/json",
                accept="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            embedding = np.array(response_body['embedding'], dtype=np.float32)
            return embedding
            
        except Exception as e:
            logger.error(f"Erreur lors de l'appel à Bedrock: {e}")
            # Fallback vers le modèle local
            if hasattr(self, 'embedding_model'):
                return self.embedding_model.encode(text)
            else:
                raise e
    
    def get_embedding_local(self, text: str) -> np.ndarray:
        """Obtient un embedding via le modèle local"""
        return self.embedding_model.encode(text)
    
    def get_embedding(self, text: str) -> np.ndarray:
        """Interface unifiée pour obtenir des embeddings"""
        if self.use_bedrock:
            return self.get_embedding_bedrock(text)
        else:
            return self.get_embedding_local(text)
    
    def load_data(self, 
                  articles_file: str = "/workspaces/SmarBot/data/json/diagnostic_articles.json",
                  garages_file: str = "/workspaces/SmarBot/data/json/garages.json"):
        """Charge les données JSON"""
        logger.info("Chargement des données...")
        
        with open(articles_file, 'r', encoding='utf-8') as f:
            self.articles = json.load(f)
        
        with open(garages_file, 'r', encoding='utf-8') as f:
            self.garages = json.load(f)
        
        logger.info(f"Données chargées: {len(self.articles)} articles, {len(self.garages)} garages")
    
    def create_embeddings(self) -> None:
        """Crée les embeddings pour tous les articles"""
        logger.info("Création des embeddings...")
        
        embeddings = []
        self.metadata = []
        
        for article in self.articles:
            # Texte pour l'embedding : combinaison optimisée
            embedding_text = self._create_embedding_text(article)
            
            # Génération de l'embedding
            embedding = self.get_embedding(embedding_text)
            embeddings.append(embedding)
            
            # Métadonnées pour la recherche
            metadata = {
                'article_id': article['article_id'],
                'type': 'diagnostic_article',
                'vehicle_manufacturer': article['vehicle_info']['manufacturer'],
                'vehicle_model': article['vehicle_info']['model'],
                'vehicle_year': article['vehicle_info']['year'],
                'obd_codes': [code['code'] for code in article['obd_codes']],
                'symptom': article['symptom'],
                'estimated_price': article['estimated_price'],
                'estimated_duration': article['estimated_duration'],
                'embedding_text': embedding_text
            }
            self.metadata.append(metadata)
        
        # Création de l'index FAISS
        embeddings_array = np.array(embeddings, dtype=np.float32)
        
        # Utilisation de IndexFlatIP pour la similarité cosinus
        self.index = faiss.IndexFlatIP(self.embedding_dimension)
        
        # Normalisation pour la similarité cosinus
        faiss.normalize_L2(embeddings_array)
        self.index.add(embeddings_array)
        
        logger.info(f"Index FAISS créé avec {self.index.ntotal} vecteurs")
    
    def _create_embedding_text(self, article: Dict[str, Any]) -> str:
        """Crée un texte optimisé pour l'embedding"""
        parts = []
        
        # Informations véhicule
        if article['vehicle_info']['manufacturer']:
            parts.append(f"メーカー: {article['vehicle_info']['manufacturer']}")
        if article['vehicle_info']['model']:
            parts.append(f"車種: {article['vehicle_info']['model']}")
        if article['vehicle_info']['year']:
            parts.append(f"年式: {article['vehicle_info']['year']}年")
        
        # Codes OBD
        if article['obd_codes']:
            obd_info = []
            for code_info in article['obd_codes']:
                obd_info.append(f"{code_info['code']} {code_info['description']}")
            parts.append(f"故障コード: {', '.join(obd_info)}")
        
        # Symptôme
        if article['symptom']:
            parts.append(f"症状: {article['symptom']}")
        
        # Diagnostic
        if article['diagnosis']:
            parts.append(f"診断: {article['diagnosis']}")
        
        # Solution
        if article['solution']:
            parts.append(f"対処法: {article['solution']}")
        
        # Résumé comme contexte additionnel
        if article['summary']:
            parts.append(f"要約: {article['summary']}")
        
        return " | ".join(parts)
    
    def search(self, 
               query: str, 
               k: int = 5,
               min_similarity: float = 0.3) -> List[Dict[str, Any]]:
        """Recherche sémantique dans les articles"""
        if self.index is None:
            raise ValueError("Index non initialisé. Appelez create_embeddings() d'abord.")
        
        # Génération de l'embedding de la requête
        query_embedding = self.get_embedding(query)
        query_embedding = query_embedding.reshape(1, -1)
        
        # Normalisation pour la similarité cosinus
        faiss.normalize_L2(query_embedding)
        
        # Recherche
        similarities, indices = self.index.search(query_embedding, k)
        
        # Formatage des résultats
        results = []
        for i, (similarity, idx) in enumerate(zip(similarities[0], indices[0])):
            if similarity >= min_similarity:
                article = self.articles[idx]
                metadata = self.metadata[idx]
                
                result = {
                    'rank': i + 1,
                    'similarity': float(similarity),
                    'article': article,
                    'metadata': metadata,
                    'relevance_explanation': self._explain_relevance(query, article, similarity)
                }
                results.append(result)
        
        return results
    
    def _explain_relevance(self, query: str, article: Dict[str, Any], similarity: float) -> str:
        """Explique pourquoi cet article est pertinent"""
        explanations = []
        
        query_lower = query.lower()
        
        # Vérification du véhicule
        if article['vehicle_info']['manufacturer'] and \
           article['vehicle_info']['manufacturer'].lower() in query_lower:
            explanations.append(f"メーカー一致: {article['vehicle_info']['manufacturer']}")
        
        # Vérification des codes OBD
        for code_info in article['obd_codes']:
            if code_info['code'].lower() in query_lower:
                explanations.append(f"故障コード一致: {code_info['code']}")
        
        # Vérification des symptômes
        if article['symptom'] and any(word in query_lower for word in article['symptom'].split()):
            explanations.append(f"症状関連: {article['symptom']}")
        
        # Score de similarité
        if similarity > 0.8:
            relevance = "非常に関連性が高い"
        elif similarity > 0.6:
            relevance = "関連性が高い"
        elif similarity > 0.4:
            relevance = "関連性がある"
        else:
            relevance = "部分的に関連"
        
        explanations.append(f"類似度: {similarity:.3f} ({relevance})")
        
        return " | ".join(explanations)
    
    def find_nearby_garages(self, 
                           location: str = None,
                           vehicle_manufacturer: str = None,
                           service_type: str = None) -> List[Dict[str, Any]]:
        """ガレージの検索 (簡易版 - 実際にはより高度な地理的検索が必要)"""
        filtered_garages = []
        
        for garage in self.garages:
            match_score = 0
            reasons = []
            
            # Localisation
            if location and location in garage['adresse']:
                match_score += 3
                reasons.append(f"地域一致: {location}")
            
            # Spécialité véhicule
            if vehicle_manufacturer and vehicle_manufacturer in garage.get('specialites', []):
                match_score += 2
                reasons.append(f"メーカー専門: {vehicle_manufacturer}")
            
            # Type de service
            if service_type and service_type in garage.get('services', []):
                match_score += 1
                reasons.append(f"サービス対応: {service_type}")
            
            if match_score > 0 or not any([location, vehicle_manufacturer, service_type]):
                garage_result = garage.copy()
                garage_result['match_score'] = match_score
                garage_result['match_reasons'] = reasons
                filtered_garages.append(garage_result)
        
        # Tri par score de correspondance
        filtered_garages.sort(key=lambda x: x['match_score'], reverse=True)
        
        return filtered_garages[:5]  # Top 5
    
    def save_index(self, index_dir: str = "/workspaces/SmarBot/data/faiss_index"):
        """Sauvegarde l'index FAISS et les métadonnées"""
        Path(index_dir).mkdir(parents=True, exist_ok=True)
        
        if self.index is not None:
            # Sauvegarde de l'index FAISS
            index_file = Path(index_dir) / "articles.index"
            faiss.write_index(self.index, str(index_file))
            
            # Sauvegarde des métadonnées
            metadata_file = Path(index_dir) / "metadata.pkl"
            with open(metadata_file, 'wb') as f:
                pickle.dump(self.metadata, f)
            
            logger.info(f"Index sauvegardé dans {index_dir}")
    
    def load_index(self, index_dir: str = "/workspaces/SmarBot/data/faiss_index"):
        """Charge l'index FAISS et les métadonnées"""
        index_file = Path(index_dir) / "articles.index"
        metadata_file = Path(index_dir) / "metadata.pkl"
        
        if index_file.exists() and metadata_file.exists():
            self.index = faiss.read_index(str(index_file))
            
            with open(metadata_file, 'rb') as f:
                self.metadata = pickle.load(f)
            
            logger.info(f"Index chargé depuis {index_dir}")
            return True
        return False

if __name__ == '__main__':
    # Test du système de recherche
    search_engine = GoonetVectorSearch(use_bedrock=False)
    
    # Chargement des données
    search_engine.load_data()
    
    # Création des embeddings
    search_engine.create_embeddings()
    
    # Sauvegarde
    search_engine.save_index()
    
    # Test de recherche
    test_queries = [
        "ホンダのN-BOXでハンドルが重い",
        "トヨタ プリウス エンジン警告灯",
        "U3003 バッテリー 異常",
        "エアコンが効かない 修理"
    ]
    
    print("\n🔍 Tests de recherche:")
    for query in test_queries:
        print(f"\n📝 Requête: {query}")
        results = search_engine.search(query, k=3)
        
        for result in results:
            print(f"  📄 [{result['rank']}] Article {result['article']['article_id']}")
            print(f"      🎯 Similarité: {result['similarity']:.3f}")
            print(f"      🚗 Véhicule: {result['article']['vehicle_info']['manufacturer']} {result['article']['vehicle_info']['model']} ({result['article']['vehicle_info']['year']})")
            print(f"      🚨 Codes OBD: {[c['code'] for c in result['article']['obd_codes']]}")
            print(f"      💡 Pertinence: {result['relevance_explanation']}")
    
    print("\n✅ Tests de recherche vectorielle terminés!")

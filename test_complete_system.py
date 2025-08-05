#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test complet pour le chatbot Goo-net Pit
Valide toutes les fonctionnalités du système
"""

import requests
import json
import time
import sys
from typing import Dict, Any

API_BASE_URL = "http://localhost:8001"
FRONTEND_URL = "http://localhost:3000"

def test_api_health() -> bool:
    """Test de l'état de santé de l'API"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Health: {data['status']}")
            print(f"   Index size: {data.get('index_size', 'N/A')}")
            print(f"   Components: {data['components']}")
            return True
        else:
            print(f"❌ API Health failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API Health error: {e}")
        return False

def test_search_endpoint() -> bool:
    """Test de l'endpoint de recherche"""
    try:
        payload = {
            "query": "U3003 バッテリー電圧異常",
            "max_results": 3,
            "min_similarity": 0.3
        }
        
        response = requests.post(
            f"{API_BASE_URL}/search",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Search: {data['results_count']} résultats trouvés")
            
            if data['results']:
                first_result = data['results'][0]
                print(f"   Premier résultat: Article {first_result['article']['article_id']}")
                print(f"   Similarité: {first_result['similarity']:.3f}")
                print(f"   Véhicule: {first_result['article']['vehicle_info']['manufacturer']} {first_result['article']['vehicle_info']['model']}")
            
            return True
        else:
            print(f"❌ Search failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Search error: {e}")
        return False

def test_chat_endpoint() -> bool:
    """Test de l'endpoint de chat"""
    test_messages = [
        "ホンダのN-BOXでハンドルが重いです",
        "トヨタ プリウス エンジン警告灯が点灯",
        "U3003-1Cというエラーコード",
        "エアコンが効かない 東京"
    ]
    
    success_count = 0
    
    for i, message in enumerate(test_messages, 1):
        try:
            payload = {
                "message": message,
                "session_id": f"test-session-{i}"
            }
            
            print(f"\n🔍 Test Chat {i}: {message}")
            
            response = requests.post(
                f"{API_BASE_URL}/chat",
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Réponse reçue (confidence: {data['confidence']:.3f})")
                print(f"   📚 Sources: {len(data['sources'])} articles")
                print(f"   🏪 Garages recommandés: {len(data['recommendations'])}")
                
                if data.get('follow_up_questions'):
                    print(f"   ❓ Questions de suivi: {len(data['follow_up_questions'])}")
                
                # Affichage du début de la réponse
                response_preview = data['message'][:100] + "..." if len(data['message']) > 100 else data['message']
                print(f"   💬 Début de réponse: {response_preview}")
                
                success_count += 1
                
            else:
                print(f"   ❌ Échec: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    
    print(f"\n📊 Résumé Chat: {success_count}/{len(test_messages)} tests réussis")
    return success_count == len(test_messages)

def test_garages_endpoint() -> bool:
    """Test de l'endpoint garages"""
    try:
        # Test sans filtres
        response = requests.get(f"{API_BASE_URL}/garages", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Garages: {data['garages_count']} garages trouvés")
            
            # Test avec filtres
            response_filtered = requests.get(
                f"{API_BASE_URL}/garages?manufacturer=ホンダ&location=東京",
                timeout=10
            )
            
            if response_filtered.status_code == 200:
                filtered_data = response_filtered.json()
                print(f"   Avec filtres: {filtered_data['garages_count']} garages")
                return True
            
        print(f"❌ Garages failed: {response.status_code}")
        return False
        
    except Exception as e:
        print(f"❌ Garages error: {e}")
        return False

def test_frontend_availability() -> bool:
    """Test de disponibilité du frontend"""
    try:
        response = requests.get(f"{FRONTEND_URL}/goonet-chat.html", timeout=10)
        
        if response.status_code == 200 and "Goo-net Pit" in response.text:
            print("✅ Frontend: Interface accessible")
            return True
        else:
            print(f"❌ Frontend failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Frontend error: {e}")
        return False

def test_stats_endpoint() -> bool:
    """Test de l'endpoint de statistiques"""
    try:
        response = requests.get(f"{API_BASE_URL}/stats", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Stats: Version {data['api_version']}")
            print(f"   Conversations: {data['total_conversations']}")
            
            db_stats = data.get('database_stats', {})
            print(f"   Articles: {db_stats.get('total_articles', 'N/A')}")
            print(f"   Garages: {db_stats.get('total_garages', 'N/A')}")
            print(f"   Index vectoriel: {db_stats.get('vector_index_size', 'N/A')}")
            
            return True
        else:
            print(f"❌ Stats failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Stats error: {e}")
        return False

def test_feedback_endpoint() -> bool:
    """Test de l'endpoint de feedback"""
    try:
        payload = {
            "response_id": "test-response-123",
            "rating": 5,
            "comment": "Excellent service de diagnostic!"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/feedback",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Feedback: {data['message']}")
            return True
        else:
            print(f"❌ Feedback failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Feedback error: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚗 Tests du Système Goo-net Pit Chatbot")
    print("=" * 50)
    
    # Attendre que les services soient disponibles
    print("⏳ Attente de la disponibilité des services...")
    for attempt in range(30):
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                break
        except:
            pass
        time.sleep(1)
        if attempt == 29:
            print("❌ Timeout: Services non disponibles")
            sys.exit(1)
    
    print("🚀 Services détectés, début des tests...\n")
    
    # Exécution des tests
    tests = [
        ("API Health", test_api_health),
        ("Statistics", test_stats_endpoint),
        ("Search Engine", test_search_endpoint),
        ("Garages", test_garages_endpoint),
        ("Frontend", test_frontend_availability),
        ("Feedback", test_feedback_endpoint),
        ("Chat Engine", test_chat_endpoint),  # Le plus long en dernier
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🔍 Test: {test_name}")
        print("-" * 30)
        
        start_time = time.time()
        success = test_func()
        duration = time.time() - start_time
        
        results[test_name] = {
            'success': success,
            'duration': duration
        }
        
        print(f"⏱️  Durée: {duration:.2f}s")
    
    # Résumé final
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    total_tests = len(tests)
    passed_tests = sum(1 for r in results.values() if r['success'])
    total_duration = sum(r['duration'] for r in results.values())
    
    for test_name, result in results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{status} {test_name:<15} ({result['duration']:.2f}s)")
    
    print("-" * 50)
    print(f"🎯 Score: {passed_tests}/{total_tests} tests réussis")
    print(f"⏱️  Temps total: {total_duration:.2f}s")
    
    if passed_tests == total_tests:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS!")
        print("✅ Le système Goo-net Pit est prêt pour la production")
        
        print("\n🔗 URLs d'accès:")
        print(f"   💬 Chat: {FRONTEND_URL}/goonet-chat.html")
        print(f"   📚 API Docs: {API_BASE_URL}/docs")
        print(f"   🏥 Health: {API_BASE_URL}/health")
        
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test(s) ont échoué")
        print("🔧 Vérifiez les logs pour plus de détails")
        sys.exit(1)

if __name__ == "__main__":
    main()

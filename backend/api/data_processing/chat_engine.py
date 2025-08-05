#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Moteur conversationnel intelligent pour le chatbot Goo-net Pit
Utilise AWS Bedrock avec Claude Sonnet 3.5 et la recherche vectorielle
"""

import json
import re
import boto3
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from vector_search import GoonetVectorSearch

logger = logging.getLogger(__name__)

@dataclass
class UserMessage:
    """Structure d'un message utilisateur"""
    text: str
    timestamp: datetime
    extracted_info: Dict[str, Any] = None

@dataclass
class ChatResponse:
    """Structure d'une réponse du chatbot"""
    message: str
    confidence: float
    sources: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    appointment_form: Optional[Dict[str, Any]] = None
    follow_up_questions: List[str] = None

class GoonetChatEngine:
    """Moteur de chat intelligent pour Goo-net Pit"""
    
    def __init__(self, use_bedrock: bool = True):
        self.use_bedrock = use_bedrock
        self.search_engine = GoonetVectorSearch(use_bedrock=use_bedrock)
        
        # Initialisation du client Bedrock
        if use_bedrock:
            try:
                self.bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
                logger.info("Client AWS Bedrock initialisé pour Claude")
            except Exception as e:
                logger.error(f"Erreur d'initialisation Bedrock: {e}")
                self.use_bedrock = False
        
        # Chargement des données et index
        self._initialize_search_engine()
        
        # Patterns pour l'extraction d'entités
        self.entity_patterns = {
            'manufacturer': r'(ホンダ|トヨタ|日産|マツダ|スバル|ダイハツ|スズキ|ミツビシ)',
            'model': r'(N-BOX|プリウス|セレナ|フィット|アクア|ノート|デミオ|CX-5|インプレッサ|フォレスター)',
            'year': r'(\d{4})年?',
            'obd_code': r'([PCBU][0-9A-F]{4}(?:-[0-9A-F]{1,2})?)',
            'symptoms': r'(警告灯|エアコン|ハンドル|エンジン|ブレーキ|異音|振動|効かない|重い|不調)',
            'location': r'(東京|大阪|名古屋|札幌|福岡|仙台|広島|神奈川|千葉|埼玉|北海道|青森|岩手|宮城|秋田|山形|福島|茨城|栃木|群馬|新潟|富山|石川|福井|山梨|長野|岐阜|静岡|愛知|三重|滋賀|京都|兵庫|奈良|和歌山|鳥取|島根|岡山|山口|徳島|香川|愛媛|高知|佐賀|長崎|熊本|大分|宮崎|鹿児島|沖縄)'
        }
    
    def _initialize_search_engine(self):
        """Moteur de recherche et données"""
        try:
            # Chargement des données
            self.search_engine.load_data()
            
            # Tentative de chargement de l'index existant
            if not self.search_engine.load_index():
                logger.info("Création d'un nouvel index FAISS")
                self.search_engine.create_embeddings()
                self.search_engine.save_index()
            else:
                logger.info("Index FAISS chargé avec succès")
                
        except Exception as e:
            logger.error(f"Erreur d'initialisation du moteur de recherche: {e}")
            raise e
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extraction d'entités depuis le texte utilisateur"""
        entities = {}
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                if entity_type == 'year':
                    entities[entity_type] = int(matches[0])
                elif entity_type in ['symptoms']:
                    entities[entity_type] = matches  # Garde tous les symptômes
                else:
                    entities[entity_type] = matches[0]  # Premier match pour les autres
        
        return entities
    
    def call_claude_bedrock(self, prompt: str, max_tokens: int = 2000) -> str:
        """Appel à Claude Sonnet 3.5 via AWS Bedrock"""
        try:
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "top_p": 0.9
            })
            
            response = self.bedrock_client.invoke_model(
                modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
                body=body,
                contentType="application/json",
                accept="application/json"
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
            
        except Exception as e:
            logger.error(f"Erreur lors de l'appel à Claude: {e}")
            return self._generate_fallback_response()
    
    def _generate_fallback_response(self) -> str:
        """Réponse de fallback en cas d'erreur avec Claude"""
        return """申し訳ございませんが、現在一時的にサービスに接続できません。
しばらく時間をおいてから再度お試しください。
お急ぎの場合は、最寄りのGoo-net Pit登録店舗にお電話でお問い合わせください。"""
    
    def create_diagnostic_prompt(self, 
                                user_message: str, 
                                entities: Dict[str, Any],
                                search_results: List[Dict[str, Any]]) -> str:
        """Claude用の診断プロンプトを作成"""
        
        prompt = f"""あなたは日本の自動車修理専門のAIアシスタントです。Goo-net Pitのお客様の車の問題について、実際の修理データベースに基づいて回答してください。

【お客様の相談内容】
{user_message}

【抽出された情報】
"""
        
        if entities:
            for key, value in entities.items():
                if key == 'manufacturer':
                    prompt += f"- メーカー: {value}\n"
                elif key == 'model':
                    prompt += f"- 車種: {value}\n"
                elif key == 'year':
                    prompt += f"- 年式: {value}年\n"
                elif key == 'obd_code':
                    prompt += f"- 故障コード: {value}\n"
                elif key == 'symptoms':
                    prompt += f"- 症状: {', '.join(value) if isinstance(value, list) else value}\n"
                elif key == 'location':
                    prompt += f"- 地域: {value}\n"
        
        prompt += "\n【関連する修理事例】\n"
        
        if search_results:
            for i, result in enumerate(search_results[:3], 1):
                article = result['article']
                prompt += f"\n事例{i}:\n"
                prompt += f"- 車両: {article['vehicle_info']['manufacturer']} {article['vehicle_info']['model']} ({article['vehicle_info']['year']}年)\n"
                
                if article['obd_codes']:
                    codes = [f"{code['code']} ({code['description']})" for code in article['obd_codes']]
                    prompt += f"- 故障コード: {', '.join(codes)}\n"
                
                if article['symptom']:
                    prompt += f"- 症状: {article['symptom']}\n"
                    
                if article['diagnosis']:
                    prompt += f"- 診断結果: {article['diagnosis']}\n"
                    
                if article['solution']:
                    prompt += f"- 対処法: {article['solution']}\n"
                    
                if article['estimated_price']:
                    prompt += f"- 修理費用目安: {article['estimated_price']:,}円\n"
                    
                if article['estimated_duration']:
                    prompt += f"- 作業時間目安: {article['estimated_duration']:.1f}時間\n"
        else:
            prompt += "該当する修理事例が見つかりませんでした。\n"
        
        prompt += """
【回答ガイドライン】
1. 100%日本語で回答してください
2. 抽出された情報と修理事例を基に、具体的で実用的なアドバイスを提供してください
3. 修理費用と時間の目安を含めてください
4. 安全性に関わる問題の場合は、すぐに修理店での点検を推奨してください
5. 不明な点がある場合は、追加質問を提案してください
6. 実際のデータに基づかない推測は避けてください

【回答形式】
## 診断結果
[お客様の問題に対する診断]

## 推奨対処法
[具体的な修理手順や対処法]

## 費用・時間の目安
[修理費用と作業時間の見積もり]

## 注意事項
[安全上の注意や緊急性について]

## 追加確認事項
[より正確な診断のための質問があれば]

お客様の安全と安心を最優先に、丁寧にご回答ください。"""
        
        return prompt
    
    def process_message(self, user_message: str) -> ChatResponse:
        """ユーザーメッセージを処理して回答を生成"""
        
        # 1. エンティティ抽出
        entities = self.extract_entities(user_message)
        logger.info(f"抽出されたエンティティ: {entities}")
        
        # 2. 類似事例の検索
        search_results = self.search_engine.search(user_message, k=5, min_similarity=0.3)
        logger.info(f"検索結果: {len(search_results)}件")
        
        # 3. Claude用プロンプト作成
        prompt = self.create_diagnostic_prompt(user_message, entities, search_results)
        
        # 4. Claude Sonnet 3.5による回答生成
        if self.use_bedrock:
            response_text = self.call_claude_bedrock(prompt)
        else:
            response_text = self._generate_fallback_response()
        
        # 5. ガレージ推奨の生成
        garage_recommendations = self._get_garage_recommendations(entities)
        
        # 6. 信頼度の計算
        confidence = self._calculate_confidence(search_results, entities)
        
        # 7. 予約フォームの生成
        appointment_form = self._generate_appointment_form(entities, garage_recommendations)
        
        # 8. フォローアップ質問の生成
        follow_up_questions = self._generate_follow_up_questions(entities, search_results)
        
        return ChatResponse(
            message=response_text,
            confidence=confidence,
            sources=[{'article_id': r['article']['article_id'], 
                     'similarity': r['similarity'],
                     'title': f"{r['article']['vehicle_info']['manufacturer']} {r['article']['vehicle_info']['model']} - {r['article']['summary'][:50]}..."}
                    for r in search_results[:3]],
            recommendations=garage_recommendations,
            appointment_form=appointment_form,
            follow_up_questions=follow_up_questions
        )
    
    def _get_garage_recommendations(self, entities: Dict[str, Any]) -> List[Dict[str, Any]]:
        """ガレージの推奨を生成"""
        manufacturer = entities.get('manufacturer')
        location = entities.get('location')
        
        garages = self.search_engine.find_nearby_garages(
            location=location,
            vehicle_manufacturer=manufacturer,
            service_type='修理'
        )
        
        return garages[:3]  # Top 3 garages
    
    def _calculate_confidence(self, search_results: List[Dict[str, Any]], entities: Dict[str, Any]) -> float:
        """回答の信頼度を計算"""
        if not search_results:
            return 0.3
        
        # 基本信頼度は最高の類似度
        base_confidence = search_results[0]['similarity'] if search_results else 0.3
        
        # エンティティマッチボーナス
        entity_bonus = 0.0
        if entities.get('manufacturer'):
            entity_bonus += 0.1
        if entities.get('obd_code'):
            entity_bonus += 0.2
        if entities.get('symptoms'):
            entity_bonus += 0.1
        
        # 複数の事例があるボーナス
        multiple_results_bonus = min(len(search_results) * 0.05, 0.2)
        
        confidence = min(base_confidence + entity_bonus + multiple_results_bonus, 1.0)
        return round(confidence, 3)
    
    def _generate_appointment_form(self, entities: Dict[str, Any], garages: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """予約フォームの事前入力データを生成"""
        if not garages:
            return None
        
        form_data = {
            'vehicle_manufacturer': entities.get('manufacturer'),
            'vehicle_model': entities.get('model'),
            'vehicle_year': entities.get('year'),
            'issue_description': entities.get('symptoms', []),
            'preferred_garage': garages[0]['garage_id'] if garages else None,
            'urgency': 'high' if any(keyword in str(entities.get('symptoms', '')) 
                                   for keyword in ['ブレーキ', '警告灯', 'エンジン']) else 'normal'
        }
        
        return form_data
    
    def _generate_follow_up_questions(self, entities: Dict[str, Any], search_results: List[Dict[str, Any]]) -> List[str]:
        """フォローアップ質問を生成"""
        questions = []
        
        # 不足している基本情報
        if not entities.get('manufacturer'):
            questions.append("お車のメーカー（ホンダ、トヨタなど）を教えていただけますか？")
        
        if not entities.get('model'):
            questions.append("車種名（N-BOX、プリウスなど）をお教えください。")
        
        if not entities.get('year'):
            questions.append("年式（何年製）をお教えください。")
        
        # 症状の詳細
        if not entities.get('symptoms'):
            questions.append("具体的にどのような症状でお困りですか？")
        
        # 緊急性の確認
        if entities.get('symptoms') and any(urgent in str(entities['symptoms']) 
                                           for urgent in ['警告灯', 'ブレーキ', 'エンジン']):
            questions.append("現在も運転中に症状が発生していますか？安全性に関わる可能性があります。")
        
        return questions[:3]  # 最大3つまで

# テスト用のメイン関数
if __name__ == '__main__':
    # Chat engineの初期化
    chat_engine = GoonetChatEngine(use_bedrock=False)  # テスト用にローカルモード
    
    # テスト用のメッセージ
    test_messages = [
        "ホンダのN-BOXでハンドルが重いんですが、どうしたらいいでしょうか？",
        "トヨタ プリウスでエンジン警告灯が点いています。修理費用はいくらぐらいですか？",
        "U3003-1Cというエラーコードが出ました。バッテリー関係だと思うのですが...",
        "エアコンが効かなくなりました。東京でいいお店はありますか？"
    ]
    
    print("🤖 Goo-net Pit チャットボット テスト")
    print("=" * 50)
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n💬 テスト {i}: {message}")
        print("-" * 40)
        
        response = chat_engine.process_message(message)
        
        print(f"🎯 信頼度: {response.confidence:.3f}")
        print(f"📚 参考事例: {len(response.sources)}件")
        print(f"🏪 推奨ガレージ: {len(response.recommendations)}件")
        
        if response.follow_up_questions:
            print(f"❓ フォローアップ質問:")
            for q in response.follow_up_questions:
                print(f"   - {q}")
        
        print(f"\n💡 回答:\n{response.message}")
        
        if response.appointment_form:
            print(f"\n📋 予約フォーム情報:")
            for key, value in response.appointment_form.items():
                if value:
                    print(f"   {key}: {value}")
    
    print("\n✅ チャットボットテスト完了！")

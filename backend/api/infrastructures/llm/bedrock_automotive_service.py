"""AWS Bedrock LLM service for automotive diagnostics."""

import json
from typing import Any, Dict, Generator, List, Optional

from api.domain.models.automotive.models import DiagnosticArticle, OBDCode, Vehicle
from api.domain.models.conversation.conversation_turn import Turn
from api.domain.models.data_point import DataPoint
from api.domain.models.llm import ModelName
from api.domain.services.llm import ILLMService
from api.infrastructures.llm.aws_bedrock.client import BedrockClient
from api.libs.logging import get_logger


# Automotive specialized prompts
AUTOMOTIVE_DIAGNOSTIC_PROMPT = """
あなたは日本の自動車OBD診断の専門家です。ホンダ、トヨタ、日産の車両に特化しています。

Goo-net Pitのデータを使用して以下を行ってください：
- OBDエラーコード（U3003-1C、C1AE687など）の解釈
- 修理ソリューションの提案
- 専門ガレージの推奨
- 診断ガイドの提供

常に日本語で正確な技術説明を提供してください。
"""

OBD_CODE_ANALYSIS_PROMPT = """
以下のOBDコードを分析してください：{obd_code}

車両情報：{vehicle_info}

以下の形式で回答してください：
1. コードの意味
2. 考えられる原因
3. 推奨される対処法
4. 修理の緊急度
5. 必要な工具
"""

VEHICLE_DIAGNOSTIC_PROMPT = """
車両の診断レポートを作成してください。

車両：{vehicle_make} {vehicle_model} ({vehicle_year})
検出されたコード：{obd_codes}

包括的な診断レポートを日本語で作成してください。
"""


class BedrockLLMService(ILLMService):
    """AWS Bedrock LLM service for automotive diagnostics."""
    
    def __init__(self, bedrock_client: BedrockClient) -> None:
        """Initialize the Bedrock LLM service."""
        self.bedrock_client = bedrock_client
        self.logger = get_logger()
        self.default_model = "anthropic.claude-3-haiku-20240307-v1:0"
    
    def generate_embeddings(self, text: str, use_foreign_region: bool = False) -> List[float]:
        """Generate embeddings using AWS Titan embedding model."""
        try:
            return self.bedrock_client.create_embeddings(text)
        except Exception as e:
            self.logger.error(f"Embedding generation failed: {e}")
            raise
    
    def analyze_obd_code(self, obd_code: str, vehicle: Optional[Vehicle] = None) -> str:
        """Analyze a specific OBD code and provide diagnostic information."""
        vehicle_info = "不明"
        if vehicle:
            vehicle_info = f"{vehicle.make.value} {vehicle.model} ({vehicle.year})"
        
        prompt = OBD_CODE_ANALYSIS_PROMPT.format(
            obd_code=obd_code,
            vehicle_info=vehicle_info
        )
        
        return self._generate_response(prompt)
    
    def generate_diagnostic_report(
        self, 
        vehicle: Vehicle, 
        obd_codes: List[OBDCode]
    ) -> str:
        """Generate a comprehensive diagnostic report."""
        codes_str = ", ".join([f"{code.code} ({code.description})" for code in obd_codes])
        
        prompt = VEHICLE_DIAGNOSTIC_PROMPT.format(
            vehicle_make=vehicle.make.value,
            vehicle_model=vehicle.model,
            vehicle_year=vehicle.year,
            obd_codes=codes_str
        )
        
        return self._generate_response(prompt)
    
    def generate_repair_suggestions(self, diagnostic_articles: List[DiagnosticArticle]) -> str:
        """Generate repair suggestions based on diagnostic articles."""
        context = "\n\n".join([
            f"記事 {article.article_id}: {article.summary}"
            for article in diagnostic_articles[:3]
        ])
        
        prompt = f"""
以下の診断情報に基づいて、修理の提案を行ってください：

{context}

以下の項目を含めてください：
1. 推奨される修理手順
2. 必要な部品
3. 予想される作業時間
4. 注意事項
"""
        
        return self._generate_response(prompt)
    
    def generate_automotive_chat_response(
        self, 
        user_message: str, 
        context_articles: List[DiagnosticArticle]
    ) -> Generator[str, None, None]:
        """Generate streaming chat response for automotive queries."""
        # Prepare context from articles
        context = ""
        if context_articles:
            context = "\n".join([
                f"参考資料: {article.summary}"
                for article in context_articles[:3]
            ])
        
        messages = [
            {
                "role": "system",
                "content": AUTOMOTIVE_DIAGNOSTIC_PROMPT
            },
            {
                "role": "user", 
                "content": f"コンテキスト:\n{context}\n\n質問: {user_message}"
            }
        ]
        
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "temperature": 0.2,
            "messages": messages
        }
        
        try:
            for chunk in self.bedrock_client.invoke_model_with_response_stream(
                self.default_model, body
            ):
                if "delta" in chunk and "text" in chunk["delta"]:
                    yield chunk["delta"]["text"]
                elif "message" in chunk and "content" in chunk["message"]:
                    for content in chunk["message"]["content"]:
                        if content["type"] == "text":
                            yield content["text"]
        except Exception as e:
            self.logger.error(f"Automotive chat response generation failed: {e}")
            yield f"申し訳ございませんが、エラーが発生しました: {str(e)}"
    
    def _generate_response(self, prompt: str) -> str:
        """Generate a single response using Bedrock."""
        messages = [
            {
                "role": "system",
                "content": AUTOMOTIVE_DIAGNOSTIC_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "temperature": 0.1,
            "messages": messages
        }
        
        try:
            response = self.bedrock_client.invoke_model(self.default_model, body)
            if "content" in response and len(response["content"]) > 0:
                return response["content"][0]["text"]
            return "応答を生成できませんでした。"
        except Exception as e:
            self.logger.error(f"Response generation failed: {e}")
            return f"エラーが発生しました: {str(e)}"
    
    # Legacy methods for compatibility with existing interface
    def generate_conversation_title(self, model_name: ModelName, turn_list: List[Turn]) -> Any:
        """Generate conversation title - automotive version."""
        if not turn_list or len(turn_list[0].user.root) == 0:
            return {"root": "自動車診断セッション"}
        
        first_message = turn_list[0].user.root
        prompt = f"以下の自動車診断会話に適切なタイトルを日本語で付けてください（20文字以内）: {first_message}"
        
        title = self._generate_response(prompt)
        return {"root": title.strip()}
    
    def generate_query(self, inputs: Any) -> Any:
        """Generate search queries for automotive content."""
        user_query = inputs.user_query if hasattr(inputs, 'user_query') else str(inputs)
        
        prompt = f"""
以下のユーザークエリから、自動車診断データベースを検索するための適切なキーワードを抽出してください：
{user_query}

キーワードを日本語と英語で、コンマ区切りで提供してください。
"""
        
        response = self._generate_response(prompt)
        keywords = [kw.strip() for kw in response.split(',')]
        
        return {"queries": keywords}
    
    def generate_response_with_internal_data(self, inputs: Any) -> Generator[str, None, None]:
        """Generate response using internal automotive data."""
        user_message = inputs.user_query if hasattr(inputs, 'user_query') else str(inputs)
        context_articles = inputs.context_articles if hasattr(inputs, 'context_articles') else []
        
        yield from self.generate_automotive_chat_response(user_message, context_articles)
    
    def generate_response_without_internal_data(self, inputs: Any) -> Generator[str, None, None]:
        """Generate response without internal data."""
        user_message = inputs.user_query if hasattr(inputs, 'user_query') else str(inputs)
        yield from self.generate_automotive_chat_response(user_message, [])
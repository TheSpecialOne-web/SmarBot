"""AWS Bedrock client for AI model interaction."""

import json
import os
from typing import Any, Dict, Iterator

import boto3
from botocore.exceptions import BotoCoreError, ClientError


class BedrockClient:
    """AWS Bedrock client for automotive diagnostic AI models."""
    
    def __init__(self) -> None:
        """Initialize Bedrock client with AWS credentials."""
        self.region = os.environ.get("AWS_BEDROCK_REGION", "us-east-1")
        self.bedrock_runtime = boto3.client(
            "bedrock-runtime",
            region_name=self.region,
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        )
        self.bedrock = boto3.client(
            "bedrock",
            region_name=self.region,
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        )
    
    def get_client_settings(self, model_name: str) -> Dict[str, Any]:
        """Get client settings for specific model."""
        return {
            "region_name": self.region,
            "model_id": self._get_model_id(model_name),
        }
    
    def _get_model_id(self, model_name: str) -> str:
        """Map model names to Bedrock model IDs."""
        model_mapping = {
            "gpt-3.5-turbo": "anthropic.claude-3-haiku-20240307-v1:0",
            "gpt-3.5-turbo-16k": "anthropic.claude-3-haiku-20240307-v1:0",
            "gpt-4": "anthropic.claude-3-sonnet-20240229-v1:0",
            "gpt-4-turbo": "anthropic.claude-3-sonnet-20240229-v1:0",
            # Automotive specialized models
            "automotive-diagnostic": "anthropic.claude-3-haiku-20240307-v1:0",
            "obd-analyzer": "anthropic.claude-3-haiku-20240307-v1:0",
        }
        return model_mapping.get(model_name, "anthropic.claude-3-haiku-20240307-v1:0")
    
    def invoke_model(self, model_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke a Bedrock model with given parameters."""
        try:
            response = self.bedrock_runtime.invoke_model(
                modelId=model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )
            response_body = json.loads(response["body"].read())
            return response_body
        except (BotoCoreError, ClientError) as e:
            raise Exception(f"Bedrock model invocation failed: {e}")
    
    def invoke_model_with_response_stream(
        self, model_id: str, body: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        """Invoke model with streaming response."""
        try:
            response = self.bedrock_runtime.invoke_model_with_response_stream(
                modelId=model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )
            
            for event in response["body"]:
                chunk = json.loads(event["chunk"]["bytes"])
                yield chunk
        except (BotoCoreError, ClientError) as e:
            raise Exception(f"Bedrock streaming failed: {e}")
    
    def create_embeddings(self, text: str, model_id: str = "amazon.titan-embed-text-v1") -> list[float]:
        """Create embeddings using Titan embedding model."""
        body = {
            "inputText": text,
        }
        
        try:
            response = self.bedrock_runtime.invoke_model(
                modelId=model_id,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )
            response_body = json.loads(response["body"].read())
            return response_body["embedding"]
        except (BotoCoreError, ClientError) as e:
            raise Exception(f"Bedrock embedding failed: {e}")
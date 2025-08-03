import base64
import json
import os
from typing import Dict, Optional

from google.auth import load_credentials_from_dict
from google.auth.credentials import Credentials
from google.auth.transport.requests import Request
from neollm.types import ClientSettings

from api.domain.models.llm import ModelName
from api.libs.app_env import app_env

CLAUDE_REGION_MAP = {
    ModelName.CLAUDE_3_OPUS_20240229: "us-east5",
    ModelName.CLAUDE_3_SONNET_20240229: "us-central1",
    ModelName.CLAUDE_3_HAIKU_20240307: "us-central1",
    ModelName.CLAUDE_35_SONNET_20240620: "us-east5",
    ModelName.CLAUDE_35_SONNET_V2_20241022: "us-east5",
    ModelName.CLAUDE_35_HAIKU_20241022: "us-east5",
}

GEMINI_REGION_MAP = {
    ModelName.GEMINI_10_PRO: "asia-northeast1",
    ModelName.GEMINI_15_PRO_PREVIEW_0409: "asia-northeast1",
    ModelName.GEMINI_15_PRO_001: "asia-northeast1",
    ModelName.GEMINI_15_PRO_002: "asia-northeast1",
    ModelName.GEMINI_15_FLASH_001: "asia-northeast1",
    ModelName.GEMINI_15_FLASH_002: "asia-northeast1",
    ModelName.GEMINI_20_FLASH_EXP: "us-central1",
}


class VertexAIClient:
    credentials: Optional[Credentials] = None
    project_id: Optional[str] = None

    def __init__(self) -> None:
        if app_env.is_localhost():
            self.use_service_account_key()
        # GOOGLE_CLOUD_PROJECT_NUMBERが設定されていない場合は、サービスアカウントキーを使う
        # TODO: 全ての環境でWorkload Identityを使用するようになれば、この条件は削除
        elif not os.getenv("GOOGLE_CLOUD_PROJECT_NUMBER"):
            self.use_service_account_key()
        else:
            self.project_number = self.get_env_var("GOOGLE_CLOUD_PROJECT_NUMBER")
            self.project_id = self.get_env_var("GOOGLE_CLOUD_PROJECT_ID")
            self.pool_id = self.get_env_var("GOOGLE_CLOUD_WORKLOAD_IDENTITY_POOL_ID")
            self.provider_id = self.get_env_var("GOOGLE_CLOUD_WORKLOAD_IDENTITY_PROVIDER_ID")
            self.identity_endpoint = self.get_env_var("IDENTITY_ENDPOINT")
            self.identity_header = self.get_env_var("IDENTITY_HEADER")
            self.use_workload_identity()

    def get_env_var(self, var_name: str) -> str:
        value = os.getenv(var_name)
        if not value:
            raise EnvironmentError(f"Environment variable '{var_name}' is not set.")
        return value

    def use_service_account_key(self) -> None:
        encoded_account_key = os.getenv("GCP_SERVICE_ACCOUNT_KEY", "")
        if not encoded_account_key:
            # Claudeを使わない場合もあるので、エラーにしない
            return
        service_account_info = json.loads(base64.b64decode(encoded_account_key).decode("utf-8"))
        if not service_account_info:
            raise Exception("GCP_SERVICE_ACCOUNT_KEY is not set.")
        credentials, project_id = load_credentials_from_dict(
            info=service_account_info,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        self.credentials = credentials
        self.project_id = project_id

    def use_workload_identity(self) -> None:
        if not self.project_number:
            # Claudeを使わない場合もあるので、エラーにしない
            return
        workload_identity_info: Dict[str, object] = {
            "universal_domain": "googleapis.com",
            "type": "external_account",
            "audience": f"//iam.googleapis.com/projects/{self.project_number}/locations/global/workloadIdentityPools/{self.pool_id}/providers/{self.provider_id}",
            "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
            "token_url": "https://sts.googleapis.com/v1/token",
            "credential_source": {
                "url": f"{self.identity_endpoint}?resource=https://vault.azure.net&api-version=2019-08-01",
                "headers": {
                    "X-IDENTITY-HEADER": self.identity_header,
                },
                "format": {"type": "json", "subject_token_field_name": "access_token"},
            },
        }
        credentials, _ = load_credentials_from_dict(
            info=workload_identity_info, scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        self.credentials = credentials

    def get_client_settings_for_claude(self, model_name: ModelName) -> ClientSettings:
        if not self.credentials or not self.project_id:
            raise Exception("Vertex AI client is not initialized.")

        try:
            region = CLAUDE_REGION_MAP[model_name]
        except KeyError:
            raise Exception(f"Model {model_name} is not on GCP")
        self.credentials.refresh(Request())
        return {
            "project_id": self.project_id,
            "region": region,
            "access_token": self.credentials.token,
        }

    def get_client_settings_for_gemini(self, model_name: ModelName) -> ClientSettings:
        if not self.credentials or not self.project_id:
            raise Exception("Vertex AI client is not initialized.")

        try:
            region = GEMINI_REGION_MAP[model_name]
        except KeyError:
            raise Exception(f"Model {model_name} is not on GCP")
        self.credentials.refresh(Request())
        return {
            "project": self.project_id,
            "location": region,
            "credentials": self.credentials,
        }

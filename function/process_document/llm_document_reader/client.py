import base64
import json
import os

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.identity import DefaultAzureCredential
from google.auth import load_credentials_from_dict
from google.auth.transport.requests import Request
from neollm.types import ClientSettings

DOCUMENT_INTELLIGENCE_SERVICE = os.environ.get("DOCUMENT_INTELLIGENCE_SERVICE")

azure_credential = DefaultAzureCredential()
credentials = None
project_id = None


def init_vertexai():
    global credentials, project_id
    encoded_account_key = os.getenv("GCP_SERVICE_ACCOUNT_KEY", "")
    service_account_info = json.loads(base64.b64decode(encoded_account_key).decode("utf-8"))
    if service_account_info == {}:
        raise Exception("GCP_SERVICE_ACCOUNT_KEY is not set.")
    credentials, project_id = load_credentials_from_dict(
        info=service_account_info,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )


def get_client_settings() -> ClientSettings:
    if credentials is None or project_id is None:
        raise Exception("GCP_SERVICE_ACCOUNT_KEY is not set.")
    credentials.refresh(Request())
    return {
        "project": project_id,
        "location": "asia-northeast1",
        "credentials": credentials,
    }


def get_form_recognizer():
    return DocumentIntelligenceClient(
        endpoint=f"https://{DOCUMENT_INTELLIGENCE_SERVICE}.cognitiveservices.azure.com/",
        credential=azure_credential,
    )

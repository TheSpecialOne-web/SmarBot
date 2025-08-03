from azure.identity import DefaultAzureCredential
from fastapi import Depends
from injector import Injector
from sqlalchemy.orm import Session

from api.database import get_db_session_from_request
from api.infrastructures.ai_vision.provider import AiVisionModule
from api.infrastructures.auth0.provider import Auth0Module
from api.infrastructures.bing_search.provider import BingSearchModule
from api.infrastructures.blob_storage.provider import BlobStorageModule
from api.infrastructures.box.provider import BoxModule
from api.infrastructures.cognitive_search.provider import CognitiveSearchModule
from api.infrastructures.document_intelligence.provider import DocumentIntelligenceModule
from api.infrastructures.llm.provider import LLMModule
from api.infrastructures.metabase.provider import MetabaseModule
from api.infrastructures.msgraph.provider import MsgraphModule
from api.infrastructures.postgres.provider import PostgresModule
from api.infrastructures.queue_storage.provider import QueueStorageModule
from api.infrastructures.web_scraping.provider import WebScrapingModule

azure_credential = DefaultAzureCredential()


def get_injector(
    session: Session = Depends(get_db_session_from_request),  # noqa: B008
) -> Injector:
    return Injector(
        [
            AiVisionModule(azure_credential),
            Auth0Module(),
            BingSearchModule(),
            BlobStorageModule(azure_credential),
            BoxModule(),
            CognitiveSearchModule(azure_credential),
            DocumentIntelligenceModule(azure_credential),
            LLMModule(azure_credential),
            PostgresModule(session),
            QueueStorageModule(azure_credential),
            MsgraphModule(),
            WebScrapingModule(),
            MetabaseModule(),
        ]
    )

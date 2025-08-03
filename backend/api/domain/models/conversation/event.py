from enum import Enum


class Event(str, Enum):
    CONVERSATION_STARTED = "conversation_started"
    CONVERSATION_COMPLETED = "conversation_completed"
    QUERY_GENERATION_STARTED = "query_generation_started"
    QUERY_GENERATION_COMPLETED = "query_generation_completed"
    WEB_DOCUMENTS_RETRIEVAL_STARTED = "web_documents_retrieval_started"
    WEB_DOCUMENTS_RETRIEVAL_COMPLETED = "web_documents_retrieval_completed"
    INTERNAL_DOCUMENTS_RETRIEVAL_STARTED = "internal_documents_retrieval_started"
    INTERNAL_DOCUMENTS_RETRIEVAL_COMPLETED = "internal_documents_retrieval_completed"
    RESPONSE_GENERATION_STARTED = "response_generation_started"
    RESPONSE_GENERATION_COMPLETED = "response_generation_completed"
    PROMPT_GENERATION_STARTED = "prompt_generation_started"
    PROMPT_GENERATION_COMPLETED = "prompt_generation_completed"
    IMAGE_GENERATION_STARTED = "image_generation_started"
    IMAGE_GENERATION_COMPLETED = "image_generation_completed"

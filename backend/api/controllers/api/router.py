from fastapi import APIRouter, Depends

from api.middleware.api.dependencies import validate_api_key

from .chat_completion import chat_completion_router
from .document import document_router
from .question_answer import question_answer_router
from .endpoint import endpoint_router

external_api_router = APIRouter(dependencies=[Depends(validate_api_key)])
external_api_router.include_router(chat_completion_router)
external_api_router.include_router(document_router)
external_api_router.include_router(question_answer_router)
external_api_router.include_router(endpoint_router)

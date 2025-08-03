import json
from typing import Generator
from uuid import UUID

from anthropic import APIStatusError
from fastapi import APIRouter, Body, Depends, Path, Request, Response
from fastapi.responses import StreamingResponse
from injector import Injector

from api.dependency_injector import get_injector
from api.domain.models import (
    bot as bot_domain,
    chat_completion as chat_completion_domain,
)
from api.libs.ctx import (
    get_api_key_from_request,
    get_bot_from_request,
    get_tenant_from_request,
    get_trace_id_from_request,
)
from api.libs.error_handlers import ErrorHandlers
from api.libs.exceptions import BadRequest, HTTPException
from api.usecase.chat_completion import (
    ChatCompletionAnswer,
    ChatCompletionDataPoints,
    ChatCompletionId,
    ChatCompletionUseCase,
    CreateChatCompletionInput,
    CreateChatCompletionStreamOutput,
    IChatCompletionUseCase,
    UpdateChatCompletionFeedbackCommentInput,
    UpdateChatCompletionFeedbackEvaluationInput,
)

from .openapi import models


def get_chat_completion_interactor(
    injector: Injector = Depends(get_injector),  # noqa: B008
) -> IChatCompletionUseCase:
    return injector.get(ChatCompletionUseCase)


chat_completion_router = APIRouter()


@chat_completion_router.post(
    "/endpoints/{endpoint_id}/chat/completions", dependencies=[], response_model=models.CreateChatCompletionResponse
)
def create_chat_completion(
    request: Request,
    chat_completion_interactor: IChatCompletionUseCase = Depends(get_chat_completion_interactor),  # noqa: B008
    endpoint_id: UUID = Path(...),  # noqa: B008
    params: models.CreateChatCompletionRequest = Body(...),  # noqa: B008
):
    tenant = get_tenant_from_request(request)
    if not tenant.enable_api_integrations.root:
        raise BadRequest("API integrations are disabled")

    bot = get_bot_from_request(request)
    if bot.endpoint_id != bot_domain.EndpointId(root=endpoint_id):
        raise BadRequest("Endpoint is invalid")

    api_key = get_api_key_from_request(request)

    inputs = CreateChatCompletionInput(
        tenant=tenant,
        bot=bot,
        api_key=api_key,
        chat_completion=chat_completion_domain.ChatCompletionForCreate(
            messages=chat_completion_domain.Messages(
                root=[
                    chat_completion_domain.Message(
                        role=chat_completion_domain.Role(message.role),
                        content=chat_completion_domain.Content(root=message.content),
                    )
                    for message in params.messages
                ]
            ),
        ),
    )

    if params.stream:
        stream = chat_completion_interactor.create_chat_completion_stream(inputs)
        trace_id = get_trace_id_from_request(request)
        return StreamingResponse(
            _format_stream_response(stream, trace_id),
            media_type="application/json",
        )
    out = chat_completion_interactor.create_chat_completion(inputs)
    return models.CreateChatCompletionResponse(
        id=out.id.root,
        content=out.answer.root,
        data_points=[
            models.DataPoint(
                document_id=d.document_id.value if d.document_id else None,
                question_answer_id=d.question_answer_id.root if d.question_answer_id else None,
                cite_number=d.cite_number.root,
                chunk_name=d.chunk_name.root,
                file_name=d.blob_path.root,
                content=d.content.root,
                page_number=d.page_number.root,
                type=models.DataPointType(d.type.value),
            )
            for d in out.data_points
        ],
    )


@chat_completion_router.patch("/endpoints/{endpoint_id}/completions/{completion_id}/evaluation", dependencies=[])
def update_chat_completion_feedback_evaluation(
    request: Request,
    chat_completion_interactor: IChatCompletionUseCase = Depends(get_chat_completion_interactor),  # noqa: B008
    endpoint_id: UUID = Path(...),  # noqa: B008
    completion_id: UUID = Path(...),  # noqa: B008
    params: models.UpdateChatCompletionFeedbackEvaluationRequest = Body(...),  # noqa: B008
):
    tenant = get_tenant_from_request(request)
    if not tenant.enable_api_integrations.root:
        raise BadRequest("API integrations are disabled")

    bot = get_bot_from_request(request)
    if bot.endpoint_id != bot_domain.EndpointId(root=endpoint_id):
        raise BadRequest("Endpoint is invalid")

    chat_completion_id = chat_completion_domain.Id(root=completion_id)

    chat_completion_interactor.update_chat_completion_feedback_evaluation(
        UpdateChatCompletionFeedbackEvaluationInput(
            id=chat_completion_id, evaluation=chat_completion_domain.Evaluation(params.evaluation)
        )
    )
    return Response(status_code=200)


@chat_completion_router.patch("/endpoints/{endpoint_id}/completions/{completion_id}/comment", dependencies=[])
def update_chat_completion_feedback_comment(
    request: Request,
    chat_completion_interactor: IChatCompletionUseCase = Depends(get_chat_completion_interactor),  # noqa: B008
    endpoint_id: UUID = Path(...),  # noqa: B008
    completion_id: UUID = Path(...),  # noqa: B008
    params: models.UpdateChatCompletionFeedbackCommentRequest = Body(...),  # noqa: B008
):
    tenant = get_tenant_from_request(request)
    if not tenant.enable_api_integrations.root:
        raise BadRequest("API integrations are disabled")

    bot = get_bot_from_request(request)
    if bot.endpoint_id != bot_domain.EndpointId(root=endpoint_id):
        raise BadRequest("Endpoint is invalid")

    chat_completion_id = chat_completion_domain.Id(root=completion_id)

    chat_completion_interactor.update_chat_completion_feedback_comment(
        UpdateChatCompletionFeedbackCommentInput(
            id=chat_completion_id,
            comment=chat_completion_domain.Comment(root=params.comment),
        )
    )
    return Response(status_code=200)


def _format_stream_response(generator: CreateChatCompletionStreamOutput, trace_id: UUID) -> Generator[str, None, None]:
    error_handlers = ErrorHandlers()
    try:
        chat_completion_id = None
        answer = ""
        data_points: list[models.DataPoint] = []
        for item in generator:
            if isinstance(item, ChatCompletionId):
                chat_completion_id = item.id.root
                res = models.CreateChatCompletionResponse(
                    id=chat_completion_id,
                    content="",
                    data_points=[],
                )
                yield res.model_dump_json() + "\n"
            elif isinstance(item, ChatCompletionAnswer) and chat_completion_id is not None:
                res = models.CreateChatCompletionResponse(
                    id=chat_completion_id,
                    content=item.answer.root,
                    data_points=data_points,
                )
                yield res.model_dump_json() + "\n"
            elif isinstance(item, ChatCompletionDataPoints) and chat_completion_id is not None:
                data_points = [
                    models.DataPoint(
                        document_id=d.document_id.value if d.document_id else None,
                        question_answer_id=d.question_answer_id.root if d.question_answer_id else None,
                        cite_number=d.cite_number.root,
                        chunk_name=d.chunk_name.root,
                        file_name=d.blob_path.root,
                        content=d.content.root,
                        page_number=d.page_number.root,
                        type=models.DataPointType(d.type.value),
                    )
                    for d in item.data_points
                ]
                res = models.CreateChatCompletionResponse(
                    id=chat_completion_id,
                    content=answer,
                    data_points=data_points,
                )
                yield res.model_dump_json() + "\n"

    except Exception as e:
        internal_error_message_to_yield = (
            "チャット中にエラーが発生しました。\n\n時間をおいてやり直すか、質問内容を変えてください。"
        )
        if isinstance(e, HTTPException) and e.status_code >= 400 and e.status_code < 500:
            yield json.dumps({"error": e.detail or ""}) + "\n"
            return error_handlers.handle_client_error(e, trace_id)
        if isinstance(e, APIStatusError) and "overloaded_error" in e.message:
            yield json.dumps({"error": internal_error_message_to_yield}) + "\n"
            return error_handlers.handle_over_loaded_error(e, trace_id)
        yield json.dumps({"error": internal_error_message_to_yield}) + "\n"
        return error_handlers.handle_internal_error(e, trace_id)

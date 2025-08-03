from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.database import get_db_session_from_request
from api.domain.models import (
    api_key as ak_domain,
    bot as bot_domain,
)
from api.infrastructures.postgres.api_key import ApiKeyRepository
from api.infrastructures.postgres.bot import BotRepository
from api.libs.api_log import log_external_api_access
from api.libs.ctx import set_api_key_to_request, set_bot_to_request, set_tenant_to_request
from api.libs.exceptions import BadRequest, Forbidden
from api.libs.logging import get_logger
from api.libs.url_rule import get_url_rule_from_request

logger = get_logger()


X_NEOAI_CHAT_CLIENT_ID_HEADER = "X-neoAI-Chat-Client-Id"

security = HTTPBearer(auto_error=False)


def validate_api_key(
    request: Request,
    token: HTTPAuthorizationCredentials | None = Depends(security),  # noqa: B008
) -> None:
    if request.method == "OPTIONS":
        return

    endpoint_id = request.path_params.get("endpoint_id")
    if not endpoint_id:
        raise BadRequest("Endpoint is required")
    try:
        endpoint_id = bot_domain.EndpointId(root=UUID(endpoint_id))
    except Exception:
        raise BadRequest("Endpoint is invalid")

    if not token:
        client_id = request.headers.get(X_NEOAI_CHAT_CLIENT_ID_HEADER)
        if not client_id:
            raise BadRequest(f"Authorization header or {X_NEOAI_CHAT_CLIENT_ID_HEADER} header is required")
        api_key_id = ak_domain.Id(root=UUID(client_id))
        client_id_auth(request, endpoint_id=endpoint_id, api_key_id=api_key_id)
    else:
        session = get_db_session_from_request(request)
        api_key_repo = ApiKeyRepository(session)
        bot_repo = BotRepository(session)

        decrypted_api_key = ak_domain.DecryptedApiKey(root=token.credentials)
        api_key = api_key_repo.find_by_endpoint_id_and_decrypted_api_key(
            endpoint_id=endpoint_id,
            decrypted_api_key=decrypted_api_key,
        )
        if api_key.is_expired():
            raise BadRequest("API key is expired")
        bot = bot_repo.find_with_tenant_by_id(id=api_key.bot_id)
        if bot.endpoint_id != endpoint_id:
            raise BadRequest("Endpoint is invalid")
        tenant = bot.tenant

        set_tenant_to_request(request, tenant)
        set_bot_to_request(request, bot)
        set_api_key_to_request(request, api_key)

        log_external_api_access(
            request=request,
            logger=logger,
            tenant_id=tenant.id,
            bot_id=bot.id,
            api_key_id=api_key.id,
        )


def client_id_auth(request: Request, endpoint_id: bot_domain.EndpointId, api_key_id: ak_domain.Id):
    url_rule = get_url_rule_from_request(request)
    if not any(
        request.method == endpoint["method"] and url_rule == endpoint["url_rule"]
        for endpoint in CLIENT_ID_ONLY_ENDPOINTS
    ):
        raise Forbidden("This endpoint is not allowed to access without API key")

    session = get_db_session_from_request(request)
    api_key_repo = ApiKeyRepository(session)
    bot_repo = BotRepository(session)

    api_key = api_key_repo.find_by_id_and_endpoint_id(
        id=api_key_id,
        endpoint_id=endpoint_id,
    )
    if api_key.is_expired():
        raise BadRequest("API key is expired")
    bot = bot_repo.find_with_tenant_by_id(id=api_key.bot_id)
    if bot.endpoint_id != endpoint_id:
        raise BadRequest("Endpoint is invalid")
    tenant = bot.tenant

    set_tenant_to_request(request, tenant)
    set_bot_to_request(request, bot)
    set_api_key_to_request(request, api_key)

    log_external_api_access(
        request=request,
        logger=logger,
        tenant_id=tenant.id,
        bot_id=bot.id,
        api_key_id=api_key.id,
    )


CLIENT_ID_ONLY_ENDPOINTS = [
    {
        "method": "GET",
        "url_rule": "/endpoints/{endpoint_id}",
    },
    {
        "method": "POST",
        "url_rule": "/endpoints/{endpoint_id}/chat/completions",
    },
    {
        "method": "PATCH",
        "url_rule": "/endpoints/{endpoint_id}/completions/{completion_id}/evaluation",
    },
    {
        "method": "PATCH",
        "url_rule": "/endpoints/{endpoint_id}/completions/{completion_id}/comment",
    },
    {
        "method": "GET",
        "url_rule": "/endpoints/{endpoint_id}/documents/{document_id}/signed-url",
    },
    {
        "method": "GET",
        "url_rule": "/endpoints/{endpoint_id}/question-answers/{question_answer_id}",
    },
]

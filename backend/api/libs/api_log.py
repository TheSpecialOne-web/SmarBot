from fastapi import Request

from api.domain.models.api_key import Id as ApiKeyId
from api.domain.models.bot import Id as BotId
from api.domain.models.tenant import Id as TenantId
from api.domain.models.user import Id as UserId
from api.libs.ctx import get_trace_id_from_request
from api.libs.ip_address import get_client_ip
from api.libs.logging import StructLogger


def log_api_access(request: Request, logger: StructLogger, user_id: UserId, tenant_id: TenantId | None) -> None:
    trace_id = get_trace_id_from_request(request)
    msg = {
        "type": "api_access",
        "host": request.base_url.hostname,
        "method": request.method,
        "path": request.url.path,
        "user_id": user_id.value,
        "client_ip": get_client_ip(request),
        "trace_id": str(trace_id),
    }
    if tenant_id is not None:
        msg["tenant_id"] = tenant_id.value
    logger.info(msg)


def log_external_api_access(
    request: Request, logger: StructLogger, tenant_id: TenantId, bot_id: BotId, api_key_id: ApiKeyId
) -> None:
    trace_id = get_trace_id_from_request(request)
    msg = {
        "type": "api_access",
        "host": request.base_url.hostname,
        "method": request.method,
        "path": request.url.path,
        "tenant_id": tenant_id.value,
        "bot_id": bot_id.value,
        "api_key_id": str(api_key_id.root),
        "client_ip": get_client_ip(request),
        "trace_id": str(trace_id),
    }
    logger.info(msg)

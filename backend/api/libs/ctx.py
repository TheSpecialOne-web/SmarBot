import uuid

from fastapi import Request
from pydantic import BaseModel

from api.domain.models import (
    api_key as ak_domain,
    bot as bot_domain,
    tenant as tenant_domain,
)
from api.domain.models.tenant import Tenant
from api.domain.models.user import Email, Id, IsAdministrator, Name, Role


class ContextUser(BaseModel):
    id: Id
    name: Name
    email: Email
    tenant: Tenant
    roles: list[Role]
    is_administrator: IsAdministrator

    def is_admin(self) -> bool:
        for role in self.roles:
            if role == Role.ADMIN:
                return True
        return False

    def is_user(self) -> bool:
        for role in self.roles:
            if role == Role.USER:
                return True
        return False


def set_trace_id_to_request(request: Request) -> None:
    request.state.__setattr__("trace_id", uuid.uuid4())


def get_trace_id_from_request(request: Request) -> uuid.UUID:
    trace_id = getattr(request.state, "trace_id", None)
    if trace_id is None:
        raise ValueError("Trace ID is not set to request")
    if not isinstance(trace_id, uuid.UUID):
        raise ValueError("Trace ID is not an instance of UUID")
    return trace_id


def set_user_to_request(request: Request, user: ContextUser) -> None:
    request.state.__setattr__("user", user)


def get_user_from_request(request: Request) -> ContextUser:
    user = getattr(request.state, "user", None)
    if user is None:
        raise ValueError("User is not set to request")
    if not isinstance(user, ContextUser):
        raise ValueError("User is not an instance of ContextUser")
    return user


def set_tenant_to_request(request: Request, tenant: tenant_domain.Tenant) -> None:
    request.state.__setattr__("tenant", tenant)


def get_tenant_from_request(request: Request) -> tenant_domain.Tenant:
    tenant = getattr(request.state, "tenant", None)
    if tenant is None:
        raise ValueError("Tenant is not set to request")
    if not isinstance(tenant, tenant_domain.Tenant):
        raise ValueError("Tenant is not an instance of Tenant")
    return tenant


def set_bot_to_request(request: Request, bot: bot_domain.Bot) -> None:
    request.state.__setattr__("bot", bot)


def get_bot_from_request(request: Request) -> bot_domain.Bot:
    bot = getattr(request.state, "bot", None)
    if bot is None:
        raise ValueError("Bot is not set to request")
    if not isinstance(bot, bot_domain.Bot):
        raise ValueError("Bot is not an instance of Bot")
    return bot


def set_api_key_to_request(request: Request, api_key: ak_domain.ApiKey) -> None:
    request.state.__setattr__("api_key", api_key)


def get_api_key_from_request(request: Request) -> ak_domain.ApiKey:
    api_key = getattr(request.state, "api_key", None)
    if api_key is None:
        raise ValueError("API key is not set to request")
    if not isinstance(api_key, ak_domain.ApiKey):
        raise ValueError("API key is not an instance of ApiKey")
    return api_key

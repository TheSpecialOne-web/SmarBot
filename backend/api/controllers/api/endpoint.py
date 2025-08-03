from uuid import UUID

from fastapi import APIRouter, Path, Request

from api.domain.models import bot as bot_domain
from api.libs.ctx import get_bot_from_request
from api.libs.exceptions import BadRequest

from .openapi import models

endpoint_router = APIRouter()


@endpoint_router.get(
    "/endpoints/{endpoint_id}",
    dependencies=[],
    response_model=models.EndpointInfo,
)
def get_endpoint_info(
    request: Request,
    endpoint_id: UUID = Path(...),  # noqa: B008
):
    bot = get_bot_from_request(request)
    endpoint_id_param = bot_domain.EndpointId(root=endpoint_id)
    if bot.endpoint_id != endpoint_id_param:
        raise BadRequest("endpoint_id is invalid")

    assistant = models.Assistant(
        id=bot.id.value,
        name=bot.name.value,
        description=bot.description.value,
        icon_url=bot.icon_url.replace_base_url() if bot.icon_url is not None else None,
        icon_color=bot.icon_color.root,
    )

    return models.EndpointInfo(
        id=endpoint_id,
        assistant=assistant,
    )

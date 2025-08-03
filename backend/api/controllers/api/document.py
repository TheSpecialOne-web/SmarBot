from uuid import UUID

from fastapi import APIRouter, Depends, Path, Request
from injector import Injector

from api.dependency_injector import get_injector
from api.domain.models import (
    bot as bot_domain,
    document as document_domain,
)
from api.libs.ctx import get_bot_from_request, get_tenant_from_request
from api.libs.exceptions import BadRequest
from api.usecase.document import DocumentUseCase, IDocumentUseCase

from .openapi import models


def get_document_interactor(
    injector: Injector = Depends(get_injector),  # noqa: B008
) -> IDocumentUseCase:
    return injector.get(DocumentUseCase)


document_router = APIRouter()


@document_router.get(
    "/endpoints/{endpoint_id}/documents/{document_id}/signed-url",
    dependencies=[],
    response_model=models.DocumentSignedUrl,
)
def get_document_signed_url(
    request: Request,
    document_interactor: IDocumentUseCase = Depends(get_document_interactor),  # noqa: B008
    endpoint_id: UUID = Path(...),  # noqa: B008
    document_id: int = Path(...),
):
    tenant = get_tenant_from_request(request)
    bot = get_bot_from_request(request)
    endpoint_id_param = bot_domain.EndpointId(root=endpoint_id)
    if bot.endpoint_id != endpoint_id_param:
        raise BadRequest("endpoint_id is invalid")

    document_id_param = document_domain.Id(value=document_id)

    document = document_interactor.get_document_detail(
        tenant=tenant,
        bot_id=bot.id,
        document_id=document_id_param,
    )

    return models.DocumentSignedUrl(
        signed_url_original=document.signed_url_original.value,
        signed_url_pdf=document.signed_url_pdf.value if document.signed_url_pdf else None,
    )

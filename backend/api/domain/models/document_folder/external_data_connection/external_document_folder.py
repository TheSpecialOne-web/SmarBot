from pydantic import BaseModel

from ...tenant.external_data_connection.external_data_connection_type import ExternalDataConnectionType
from ...tenant.external_data_connection.external_id import ExternalId
from ...tenant.external_data_connection.external_updated_at import ExternalUpdatedAt
from ..name import Name


class ExternalDocumentFolder(BaseModel):
    name: Name
    external_id: ExternalId
    external_type: ExternalDataConnectionType
    external_updated_at: ExternalUpdatedAt

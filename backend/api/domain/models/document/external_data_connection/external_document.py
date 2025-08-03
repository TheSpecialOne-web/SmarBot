from pydantic import BaseModel

from ...tenant.external_data_connection.external_id import ExternalId
from ...tenant.external_data_connection.external_updated_at import ExternalUpdatedAt
from ..file_extension import FileExtension
from ..name import Name
from .external_full_path import ExternalFullPath


class ExternalDocument(BaseModel):
    name: Name
    file_extension: FileExtension
    external_id: ExternalId
    external_updated_at: ExternalUpdatedAt
    external_full_path: ExternalFullPath

import uuid

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

import api.domain.models.tenant.external_data_connection.external_data_connection as external_data_connection_domain

from .base import BaseModelWithoutDeletedAt


class ExternalDataConnection(BaseModelWithoutDeletedAt):
    __tablename__ = "external_data_connections"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, ForeignKey("tenants.id"), nullable=False)
    external_type: Mapped[str] = mapped_column(Text, nullable=False)
    encrypted_credentials: Mapped[str] = mapped_column(Text, nullable=False)

    @classmethod
    def from_external_data_connection_for_create(
        cls,
        external_data_connection: external_data_connection_domain.ExternalDataConnectionForCreate,
    ) -> "ExternalDataConnection":
        encrypted_credentials = external_data_connection.decrypted_credentials.encrypt()

        return cls(
            id=external_data_connection.id.root,
            tenant_id=external_data_connection.tenant_id.value,
            external_type=external_data_connection.external_data_connection_type.value,
            encrypted_credentials=encrypted_credentials.root,
        )

    def to_domain(self) -> external_data_connection_domain.ExternalDataConnection:
        return external_data_connection_domain.ExternalDataConnection(
            id=external_data_connection_domain.Id(root=self.id),
            tenant_id=external_data_connection_domain.TenantId(value=self.tenant_id),
            external_data_connection_type=external_data_connection_domain.ExternalDataConnectionType(
                value=self.external_type
            ),
            encrypted_credentials=external_data_connection_domain.EncryptedCredentials(
                root=self.encrypted_credentials
            ),
        )

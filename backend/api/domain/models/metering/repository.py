from abc import ABC, abstractmethod
from datetime import datetime

from api.domain.models.bot import Id as BotId
from api.domain.models.metering.bot_pdf_parser_page_count import BotPdfParserPageCount
from api.domain.models.metering.meter import PdfParserMeterForCreate
from api.domain.models.metering.quantity import Quantity
from api.domain.models.tenant import Id as TenantId
from api.domain.models.token import TokenCount


class IMeteringRepository(ABC):
    @abstractmethod
    def create_pdf_parser_count(self, metering: PdfParserMeterForCreate) -> None:
        pass

    @abstractmethod
    def get_bot_pdf_parser_page_count(
        self,
        tenant_id: TenantId,
        start_date_time: datetime,
        end_date_time: datetime,
        bot_id: BotId | None = None,
    ) -> list[BotPdfParserPageCount]:
        pass

    @abstractmethod
    def get_document_intelligence_page_count(
        self,
        tenant_id: TenantId,
        start_date_time: datetime,
        end_date_time: datetime,
    ) -> Quantity:
        pass

    @abstractmethod
    def get_document_intelligence_page_count_by_bot_id(
        self,
        tenant_id: TenantId,
        bot_id: BotId,
        start_date_time: datetime,
        end_date_time: datetime,
    ) -> Quantity:
        pass

    @abstractmethod
    def delete_by_tenant_id(self, tenant_id: TenantId) -> None:
        pass

    @abstractmethod
    def hard_delete_by_tenant_id(self, tenant_id: TenantId) -> None:
        pass

    @abstractmethod
    def get_pdf_parser_token_count_by_tenant_id(
        self,
        tenant_id: TenantId,
        start_date_time: datetime,
        end_date_time: datetime,
    ) -> TokenCount:
        pass

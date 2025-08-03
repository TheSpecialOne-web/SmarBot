from datetime import datetime, timezone

from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session, joinedload

from api.domain.models import metering as meter_domain
from api.domain.models.bot import Id as BotId
from api.domain.models.metering import (
    BotPdfParserPageCount,
    PDFParserCountType,
    Quantity,
)
from api.domain.models.tenant import Id as TenantId
from api.domain.models.token import TokenCount
from api.infrastructures.postgres.models.bot import Bot
from api.infrastructures.postgres.models.metering import Metering


class MeteringRepository(meter_domain.IMeteringRepository):
    def __init__(self, session: Session):
        self.session = session

    def create_pdf_parser_count(self, metering: meter_domain.PdfParserMeterForCreate) -> None:
        new_metering = Metering.from_domain(
            domain_model=metering,
            tenant_id=metering.tenant_id,
        )
        try:
            self.session.add(new_metering)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def get_bot_pdf_parser_page_count(
        self,
        tenant_id: TenantId,
        start_date_time: datetime,
        end_date_time: datetime,
        bot_id: BotId | None = None,
    ) -> list[BotPdfParserPageCount]:
        stmt = (
            select(
                Metering,
            )
            .join(Bot, Bot.id == Metering.bot_id)
            .where(Metering.tenant_id == tenant_id.value)
            .where(Metering.created_at >= start_date_time)
            .where(Metering.created_at < end_date_time)
            .where(Metering.type.in_(list(PDFParserCountType)))
            # workflow_idが入る場合があるが、workflowのリリース時にはこの関数自体使わないため、bot_idが存在するものだけ取得
            .where(Metering.bot_id.isnot(None))
            .options(joinedload(Metering.bot))
        )

        if bot_id is not None:
            stmt = stmt.where(Metering.bot_id == bot_id.value)

        bot_pdf_parser_token_counts = (
            self.session.execute(stmt, execution_options={"include_deleted": True}).scalars().all()
        )

        return [bot_pdf_parser_token_count.to_domain() for bot_pdf_parser_token_count in bot_pdf_parser_token_counts]

    def get_document_intelligence_page_count(
        self,
        tenant_id: TenantId,
        start_date_time: datetime,
        end_date_time: datetime,
    ) -> Quantity:
        page_count = (
            self.session.execute(
                select(Metering.quantity)
                .where(Metering.tenant_id == tenant_id.value)
                .where(Metering.type == PDFParserCountType.DOCUMENT_INTELLIGENCE_PAGE_COUNT.value)
                .where(Metering.created_at >= start_date_time)
                .where(Metering.created_at < end_date_time)
            )
            .scalars()
            .all()
        )

        return Quantity(root=sum(page_count))

    def get_document_intelligence_page_count_by_bot_id(
        self,
        tenant_id: TenantId,
        bot_id: BotId,
        start_date_time: datetime,
        end_date_time: datetime,
    ) -> Quantity:
        page_count = (
            self.session.execute(
                select(Metering.quantity)
                .where(Metering.tenant_id == tenant_id.value)
                .where(Metering.bot_id == bot_id.value)
                .where(Metering.type == PDFParserCountType.DOCUMENT_INTELLIGENCE_PAGE_COUNT.value)
                .where(Metering.created_at >= start_date_time)
                .where(Metering.created_at < end_date_time)
            )
            .scalars()
            .all()
        )

        return Quantity(root=sum(page_count))

    def delete_by_tenant_id(self, tenant_id: TenantId) -> None:
        try:
            self.session.execute(
                update(Metering)
                .where(Metering.tenant_id == tenant_id.value)
                .values(deleted_at=datetime.now(timezone.utc))
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def hard_delete_by_tenant_id(self, tenant_id: TenantId) -> None:
        try:
            self.session.execute(
                delete(Metering).where(Metering.tenant_id == tenant_id.value).where(Metering.deleted_at.isnot(None))
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def get_pdf_parser_token_count_by_tenant_id(
        self,
        tenant_id: TenantId,
        start_date_time: datetime,
        end_date_time: datetime,
    ) -> TokenCount:
        get_document_intelligence_page_count_stmt = (
            select(func.coalesce(func.sum(Metering.quantity), 0))
            .where(Metering.tenant_id == tenant_id.value)
            .where(Metering.type == PDFParserCountType.DOCUMENT_INTELLIGENCE_PAGE_COUNT.value)
            .where(Metering.created_at >= start_date_time)
            .where(Metering.created_at < end_date_time)
            .execution_options(include_deleted=True)
        )
        get_llm_document_reader_page_count_stmt = (
            select(func.coalesce(func.sum(Metering.quantity), 0))
            .where(Metering.tenant_id == tenant_id.value)
            .where(Metering.type == PDFParserCountType.LLM_DOCUMENT_READER_PAGE_COUNT.value)
            .where(Metering.created_at >= start_date_time)
            .where(Metering.created_at < end_date_time)
            .execution_options(include_deleted=True)
        )
        get_ai_vision_page_count_stmt = (
            select(func.coalesce(func.sum(Metering.quantity), 0))
            .where(Metering.tenant_id == tenant_id.value)
            .where(Metering.type == PDFParserCountType.AI_VISION_PAGE_COUNT.value)
            .where(Metering.created_at >= start_date_time)
            .where(Metering.created_at < end_date_time)
            .execution_options(include_deleted=True)
        )

        document_intelligence_token_count = (
            self.session.execute(get_document_intelligence_page_count_stmt).scalar_one()
            * PDFParserCountType.DOCUMENT_INTELLIGENCE_PAGE_COUNT.get_token_count_coefficient()
        )
        llm_document_reader_token_count = (
            self.session.execute(get_llm_document_reader_page_count_stmt).scalar_one()
            * PDFParserCountType.LLM_DOCUMENT_READER_PAGE_COUNT.get_token_count_coefficient()
        )
        ai_vision_token_count = (
            self.session.execute(get_ai_vision_page_count_stmt).scalar_one()
            * PDFParserCountType.AI_VISION_PAGE_COUNT.get_token_count_coefficient()
        )

        return TokenCount(
            root=document_intelligence_token_count + llm_document_reader_token_count + ai_vision_token_count
        )

from datetime import timedelta

from sqlalchemy import select

from api.database import SessionFactory
from api.domain.models.bot.bot import Id as Bot_Id
from api.domain.models.metering import BotPdfParserPageCount
from api.domain.models.metering.meter import PdfParserMeterForCreate, Quantity
from api.domain.models.metering.type import PDFParserCountType
from api.domain.models.tenant.tenant import (
    Id as TenantId,
    Tenant,
)
from api.infrastructures.postgres.metering import Metering, MeteringRepository
from tests.conftest import PdfParserPageMeteringSeed, TenantSeed


class TestMeteringRepository:
    def setup_method(self):
        self.session = SessionFactory()
        self.metering_repo = MeteringRepository(self.session)

    def teardown_method(self):
        self.session.close()

    def test_create_pdf_parser_count(self):
        """document_intelligenceの計測 が正常に動作するかを確認するテスト"""
        # Given
        metering = PdfParserMeterForCreate(
            type=PDFParserCountType.DOCUMENT_INTELLIGENCE_PAGE_COUNT,
            quantity=Quantity(root=5),
            bot_id=Bot_Id(value=1),
            tenant_id=TenantId(value=1),
        )

        # When
        self.metering_repo.create_pdf_parser_count(metering)

        # Then
        saved_metering = self.session.query(Metering).first()
        assert saved_metering is not None
        assert saved_metering.tenant_id == 1
        assert saved_metering.bot_id == 1
        assert saved_metering.type == PDFParserCountType.DOCUMENT_INTELLIGENCE_PAGE_COUNT
        assert saved_metering.quantity == 5

    def test_get_bot_pdf_parser_page_count(
        self,
        tenant_seed: Tenant,
        pdf_parser_page_metering_seed: PdfParserPageMeteringSeed,
    ):
        # Input
        bot_meterings, workflow_meterings, created_at, bot = pdf_parser_page_metering_seed

        # Expected
        expected_output = []
        for metering in bot_meterings:
            if type(metering.type) is not PDFParserCountType:
                continue
            expected_output.append(
                BotPdfParserPageCount(
                    bot_id=bot.id,
                    bot_name=bot.name,
                    page_count=metering.quantity,
                    count_type=metering.type,
                )
            )

        # Execute
        output = self.metering_repo.get_bot_pdf_parser_page_count(
            tenant_id=tenant_seed.id,
            # created_atの2日前
            start_date_time=created_at.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=2),
            # created_atの2日後
            end_date_time=created_at.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=2),
        )

        # Test
        assert output == expected_output

    def test_get_document_intelligence_page_count(
        self,
        tenant_seed: Tenant,
        pdf_parser_page_metering_seed: PdfParserPageMeteringSeed,
    ):
        # Given
        bot_meterings, workflow_meterings, created_at, bot = pdf_parser_page_metering_seed
        metering_list = bot_meterings + workflow_meterings
        document_intelligence_metering_list = [
            meter for meter in metering_list if meter.type == PDFParserCountType.DOCUMENT_INTELLIGENCE_PAGE_COUNT
        ]
        quantity_sum = sum([meter.quantity.root for meter in document_intelligence_metering_list])

        # When
        page_count = self.metering_repo.get_document_intelligence_page_count(
            tenant_id=tenant_seed.id,
            # created_atの2日前
            start_date_time=created_at.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=2),
            # created_atの2日後
            end_date_time=created_at.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=2),
        )

        assert page_count.root == quantity_sum

    def test_get_document_intelligence_page_count_by_bot_id(
        self,
        tenant_seed: Tenant,
        pdf_parser_page_metering_seed: PdfParserPageMeteringSeed,
    ):
        # Given
        bot_meterings, _, created_at, bot = pdf_parser_page_metering_seed
        quantity_sum = sum(
            [
                meter.quantity.root
                for meter in bot_meterings
                if meter.type == PDFParserCountType.DOCUMENT_INTELLIGENCE_PAGE_COUNT
            ]
        )

        # When
        page_count = self.metering_repo.get_document_intelligence_page_count_by_bot_id(
            tenant_id=tenant_seed.id,
            bot_id=bot.id,
            # created_atの2日前
            start_date_time=created_at.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=100),
            # created_atの2日後
            end_date_time=created_at.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=200),
        )

        assert page_count.root == quantity_sum

    def test_delete_by_tenant_id(self, pdf_parser_page_metering_seed: PdfParserPageMeteringSeed):
        bot_meterings, workflow_meterings, created_at, bot = pdf_parser_page_metering_seed
        metering_list = bot_meterings + workflow_meterings

        self.metering_repo.delete_by_tenant_id(metering_list[0].tenant_id)

        meterings = (
            self.session.execute(select(Metering).where(Metering.tenant_id == metering_list[0].tenant_id.value))
            .scalars()
            .all()
        )
        assert len(meterings) == 0

    def test_hard_delete_by_tenant_id(self, pdf_parser_page_metering_seed: PdfParserPageMeteringSeed):
        bot_meterings, workflow_meterings, created_at, bot = pdf_parser_page_metering_seed
        metering_list = bot_meterings + workflow_meterings

        self.metering_repo.delete_by_tenant_id(metering_list[0].tenant_id)
        self.metering_repo.hard_delete_by_tenant_id(metering_list[0].tenant_id)

        meterings = (
            self.session.execute(
                select(Metering)
                .where(Metering.tenant_id == metering_list[0].tenant_id.value)
                .execution_options(include_deleted=True)
            )
            .scalars()
            .all()
        )
        assert len(meterings) == 0

    def test_get_pdf_parser_token_count_by_tenant_id(
        self, tenant_seed: TenantSeed, pdf_parser_page_metering_seed: PdfParserPageMeteringSeed
    ):
        # Given
        bot_meterings, workflow_meterings, created_at, _ = pdf_parser_page_metering_seed
        metering_list = bot_meterings + workflow_meterings
        document_intelligence_token_count = sum(
            [
                meter.quantity.root * PDFParserCountType.DOCUMENT_INTELLIGENCE_PAGE_COUNT.get_token_count_coefficient()
                for meter in metering_list
                if meter.type == PDFParserCountType.DOCUMENT_INTELLIGENCE_PAGE_COUNT
            ]
        )
        llm_document_reader_token_count = sum(
            [
                meter.quantity.root * PDFParserCountType.LLM_DOCUMENT_READER_PAGE_COUNT.get_token_count_coefficient()
                for meter in metering_list
                if meter.type == PDFParserCountType.LLM_DOCUMENT_READER_PAGE_COUNT
            ]
        )

        ai_vision_token_count = sum(
            [
                meter.quantity.root * PDFParserCountType.AI_VISION_PAGE_COUNT.get_token_count_coefficient()
                for meter in metering_list
                if meter.type == PDFParserCountType.AI_VISION_PAGE_COUNT
            ]
        )
        # When
        page_count = self.metering_repo.get_pdf_parser_token_count_by_tenant_id(
            tenant_id=tenant_seed.id,
            start_date_time=created_at.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=2),
            end_date_time=created_at.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=2),
        )

        assert (
            page_count.root
            == document_intelligence_token_count + llm_document_reader_token_count + ai_vision_token_count
        )

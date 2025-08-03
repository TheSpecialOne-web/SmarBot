from enum import Enum

from pydantic import BaseModel


class MeteringType(Enum):
    DOCUMENT_INTELLIGENCE_PAGE_COUNT = "document_intelligence_page_count"
    LLM_DOCUMENT_READER_PAGE_COUNT = "llm_document_reader_page_count"
    AI_VISION_PAGE_COUNT = "ai_vision_page_count"


class Metering(BaseModel):
    tenant_id: int
    bot_id: int
    type: MeteringType
    quantity: int


def pdf_parser_metering(tenant_id: int, bot_id: int, quantity: int, pdf_parser: str) -> Metering | None:
    if pdf_parser == "ai_vision":
        return Metering(tenant_id=tenant_id, bot_id=bot_id, type=MeteringType.AI_VISION_PAGE_COUNT, quantity=quantity)
    if pdf_parser == "document_intelligence" or pdf_parser == "llm_document_reader":
        return Metering(
            tenant_id=tenant_id, bot_id=bot_id, type=MeteringType.DOCUMENT_INTELLIGENCE_PAGE_COUNT, quantity=quantity
        )
    return None


def pdf_parser_metering_v2(tenant_id: int, bot_id: int, quantity: int, pdf_parser: str) -> Metering | None:
    if pdf_parser == "ai_vision":
        type_ = MeteringType.AI_VISION_PAGE_COUNT
    elif pdf_parser == "document_intelligence":
        type_ = MeteringType.DOCUMENT_INTELLIGENCE_PAGE_COUNT
    elif pdf_parser == "llm_document_reader":
        type_ = MeteringType.LLM_DOCUMENT_READER_PAGE_COUNT
    else:
        return None

    return Metering(tenant_id=tenant_id, bot_id=bot_id, type=type_, quantity=quantity)

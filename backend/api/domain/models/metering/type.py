from enum import Enum
from typing import Union

from api.domain.models.llm import PdfParser


class PDFParserCountType(str, Enum):
    DOCUMENT_INTELLIGENCE_PAGE_COUNT = "document_intelligence_page_count"
    LLM_DOCUMENT_READER_PAGE_COUNT = "llm_document_reader_page_count"
    AI_VISION_PAGE_COUNT = "ai_vision_page_count"

    def get_token_count_coefficient(self) -> int:
        if self == self.DOCUMENT_INTELLIGENCE_PAGE_COUNT:
            return 350
        if self == self.LLM_DOCUMENT_READER_PAGE_COUNT:
            return 500
        if self == self.AI_VISION_PAGE_COUNT:
            return 35
        raise ValueError(f"PDFParserCountType に存在しない PDFParser が指定されました: {self}")

    @classmethod
    def from_pdf_parser(self, pdf_parser: PdfParser) -> "PDFParserCountType":
        if pdf_parser in [
            PdfParser.DOCUMENT_INTELLIGENCE,
            PdfParser.LLM_DOCUMENT_READER,
        ]:
            return self.DOCUMENT_INTELLIGENCE_PAGE_COUNT
        if pdf_parser == PdfParser.AI_VISION:
            return self.AI_VISION_PAGE_COUNT
        raise ValueError(f"PDFParserCountType に存在しない PDFParser が指定されました: {pdf_parser}")

    @classmethod
    def from_pdf_parser_v2(cls, pdf_parser: PdfParser) -> "PDFParserCountType":
        if pdf_parser == PdfParser.DOCUMENT_INTELLIGENCE:
            return cls.DOCUMENT_INTELLIGENCE_PAGE_COUNT
        if pdf_parser == PdfParser.LLM_DOCUMENT_READER:
            return cls.LLM_DOCUMENT_READER_PAGE_COUNT
        if pdf_parser == PdfParser.AI_VISION:
            return cls.AI_VISION_PAGE_COUNT
        raise ValueError(f"PDFParserCountType に存在しない PDFParser が指定されました: {pdf_parser}")


class FollowUpQuestionCountType(str, Enum):
    FOLLOW_UP_QUESTION_TOKEN_COUNT = "follow_up_question_token_count"


Type = Union[PDFParserCountType, FollowUpQuestionCountType]

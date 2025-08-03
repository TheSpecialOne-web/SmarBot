from enum import Enum


class PdfParser(str, Enum):
    """
    ドキュメント読み取りオプションを表すEnum
    """

    PYPDF = "pypdf"
    DOCUMENT_INTELLIGENCE = "document_intelligence"
    AI_VISION = "ai_vision"
    LLM_DOCUMENT_READER = "llm_document_reader"


class BasicAiPdfParser(str, Enum):
    """
    ドキュメント読み取りオプションを表すEnum
    """

    PYPDF = "pypdf"
    DOCUMENT_INTELLIGENCE = "document_intelligence"
    AI_VISION = "ai_vision"
    LLM_DOCUMENT_READER = "llm_document_reader"

    def to_bot_pdf_parser(self) -> PdfParser:
        match self:
            case BasicAiPdfParser.PYPDF:
                return PdfParser.PYPDF
            case BasicAiPdfParser.DOCUMENT_INTELLIGENCE:
                return PdfParser.DOCUMENT_INTELLIGENCE
            case BasicAiPdfParser.AI_VISION:
                return PdfParser.AI_VISION
            case BasicAiPdfParser.LLM_DOCUMENT_READER:
                return PdfParser.LLM_DOCUMENT_READER
            case _:
                raise ValueError(f"Unexpected BasicAiPdfParser: {self}")

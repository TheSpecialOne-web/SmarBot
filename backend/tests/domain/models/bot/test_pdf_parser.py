import pytest

from api.domain.models.llm import PdfParser


class TestPdfParser:
    def test_valid_value(self):
        pp = PdfParser("pypdf")
        assert pp.value == "pypdf"
        assert pp == PdfParser.PYPDF

        pp = PdfParser("document_intelligence")
        assert pp.value == "document_intelligence"
        assert pp == PdfParser.DOCUMENT_INTELLIGENCE

        pp = PdfParser("ai_vision")
        assert pp.value == "ai_vision"
        assert pp == PdfParser.AI_VISION

    def test_invalid_value(self):
        with pytest.raises(ValueError):
            PdfParser("nonexistent")
        with pytest.raises(ValueError):
            PdfParser("invalid")
        with pytest.raises(ValueError):
            PdfParser("parser")

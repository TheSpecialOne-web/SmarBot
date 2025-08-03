import pytest  # noqa

from api.domain.models.document import FileExtension


class TestFileExtensiion:
    def test_to_content_type(self):
        assert FileExtension.PDF.to_content_type() == "application/pdf"
        assert (
            FileExtension.XLSX.to_content_type() == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        assert (
            FileExtension.DOCX.to_content_type()
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        assert (
            FileExtension.PPTX.to_content_type()
            == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )
        assert FileExtension.TXT.to_content_type() == "text/plain; charset=utf-8"
        assert FileExtension.DOC.to_content_type() == "application/msword"
        assert FileExtension.XLS.to_content_type() == "application/vnd.ms-excel"
        assert FileExtension.PPT.to_content_type() == "application/vnd.ms-powerpoint"
        assert FileExtension.XLSM.to_content_type() == "application/vnd.ms-excel.sheet.macroenabled.12"
        assert FileExtension.XDW.to_content_type() == "application/vnd.fujifilm.fb.docuworks"

    def test_is_indexing_supported(self):
        assert FileExtension.PDF.is_indexing_supported() is True
        assert FileExtension.DOCX.is_indexing_supported() is True
        assert FileExtension.XLSX.is_indexing_supported() is True
        assert FileExtension.PPTX.is_indexing_supported() is True
        assert FileExtension.TXT.is_indexing_supported() is True
        assert FileExtension.DOC.is_indexing_supported() is False
        assert FileExtension.XLS.is_indexing_supported() is True
        assert FileExtension.PPT.is_indexing_supported() is False
        assert FileExtension.XLSM.is_indexing_supported() is False
        assert FileExtension.XDW.is_indexing_supported() is False

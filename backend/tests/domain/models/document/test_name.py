import base64
import unicodedata
import urllib.parse

import pytest

from api.domain.models.document import (
    BlobName,
    DisplayableBlobName,
    FileExtension,
    Name,
)
from api.libs.exceptions import BadRequest


class TestName:
    def test_to_encoded_name(self):
        # 正常系
        name = Name(value="テストファイル")
        expected = base64.urlsafe_b64encode(unicodedata.normalize("NFC", name.value).encode()).decode("utf-8")[:-2]
        assert name.to_encoded_name().value == expected

    def test_to_blob_name(self):
        # 正常系
        name = Name(value="テストファイル")
        expected = (
            f"{base64.urlsafe_b64encode(unicodedata.normalize('NFC', name.value).encode()).decode('utf-8')[:-2]}.pdf"
        )
        assert name.to_blob_name(FileExtension.PDF).value == expected

    def test_to_displayable_blob_name(self):
        # 正常系
        name = Name(value="テストファイル")
        expected = "テストファイル.pdf"
        assert name.to_displayable_blob_name(FileExtension.PDF).value == expected


class TestBlobName:
    def test_file_extension(self):
        # 正常系
        blob_name = BlobName(value="テストファイル.pdf")
        assert blob_name.file_extension() == FileExtension.PDF

        blob_name = BlobName(value="テストファイル.docx")
        assert blob_name.file_extension() == FileExtension.DOCX

        blob_name = BlobName(value="テストファイル.xlsx")
        assert blob_name.file_extension() == FileExtension.XLSX

        blob_name = BlobName(value="テストファイル.pptx")
        assert blob_name.file_extension() == FileExtension.PPTX

        blob_name = BlobName(value="テストファイル.txt")
        assert blob_name.file_extension() == FileExtension.TXT

        blob_name = BlobName(value="テストファイル.doc")
        assert blob_name.file_extension() == FileExtension.DOC

        blob_name = BlobName(value="テストファイル.xls")
        assert blob_name.file_extension() == FileExtension.XLS

        blob_name = BlobName(value="テストファイル.ppt")
        assert blob_name.file_extension() == FileExtension.PPT

        blob_name = BlobName(value="テストファイル.xlsm")
        assert blob_name.file_extension() == FileExtension.XLSM

        blob_name = BlobName(value="テストファイル.xdw")
        assert blob_name.file_extension() == FileExtension.XDW

        # 異常系
        blob_name = BlobName(value="テストファイル")
        with pytest.raises(BadRequest):
            blob_name.file_extension()

    def test_to_content_disposition(self):
        # 正常系
        blob_name = BlobName(value="テストファイル.pdf")
        assert blob_name.to_content_disposition() == "inline"
        blob_name = BlobName(value="テストファイル.docx")
        file_name = urllib.parse.quote("テストファイル.docx")
        assert blob_name.to_content_disposition() == "attachment;  filename={}".format(file_name)
        blob_name = BlobName(value="テストファイル.xlsx")
        file_name = urllib.parse.quote("テストファイル.xlsx")
        assert blob_name.to_content_disposition() == "attachment;  filename={}".format(file_name)
        blob_name = BlobName(value="テストファイル.pptx")
        file_name = urllib.parse.quote("テストファイル.pptx")
        assert blob_name.to_content_disposition() == "attachment;  filename={}".format(file_name)
        blob_name = BlobName(value="テストファイル.txt")
        file_name = urllib.parse.quote("テストファイル.txt")
        assert blob_name.to_content_disposition() == "inline"
        blob_name = BlobName(value="テストファイル.doc")
        file_name = urllib.parse.quote("テストファイル.doc")
        assert blob_name.to_content_disposition() == "attachment;  filename={}".format(file_name)
        blob_name = BlobName(value="テストファイル.xls")
        file_name = urllib.parse.quote("テストファイル.xls")
        assert blob_name.to_content_disposition() == "attachment;  filename={}".format(file_name)
        blob_name = BlobName(value="テストファイル.ppt")
        file_name = urllib.parse.quote("テストファイル.ppt")
        assert blob_name.to_content_disposition() == "attachment;  filename={}".format(file_name)
        blob_name = BlobName(value="テストファイル.xlsm")
        file_name = urllib.parse.quote("テストファイル.xlsm")
        assert blob_name.to_content_disposition() == "attachment;  filename={}".format(file_name)
        blob_name = BlobName(value="テストファイル.xdw")

        # 異常系
        blob_name = BlobName(value="テストファイル")
        with pytest.raises(BadRequest):
            blob_name.to_content_disposition()


class TestDisplayableBlobName:
    def test_to_blob_name(self):
        # 正常系
        displayable_blob_name = DisplayableBlobName(value="テストファイル.pdf")
        expected = f"{base64.urlsafe_b64encode(unicodedata.normalize('NFC', 'テストファイル').encode()).decode('utf-8')[:-2]}.pdf"
        assert displayable_blob_name.to_blob_name().value == expected

        # 異常系
        displayable_blob_name = DisplayableBlobName(value="テストファイル")
        with pytest.raises(BadRequest):
            displayable_blob_name.to_blob_name()

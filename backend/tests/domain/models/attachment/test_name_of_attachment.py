import pytest

from api.domain.models.attachment import BlobName, FileExtension
from api.libs.exceptions import BadRequest


class TestBlobName:
    def test_file_extension(self):
        # 正常系
        blob_name = BlobName(root="テストファイル.pdf")
        assert blob_name.file_extension() == FileExtension.PDF

        # 異常系
        blob_name = BlobName(root="テストファイル")
        with pytest.raises(BadRequest):
            blob_name.file_extension()

    def test_to_content_disposition(self):
        # 正常系
        blob_name = BlobName(root="テストファイル.pdf")
        assert blob_name.to_content_disposition() == "inline; filename=テストファイル.pdf"

        # 異常系
        blob_name = BlobName(root="テストファイル")
        with pytest.raises(BadRequest):
            blob_name.to_content_disposition()

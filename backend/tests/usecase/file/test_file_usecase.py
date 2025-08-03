import io
from unittest.mock import Mock, mock_open

import pytest

from api.domain.models import file as file_domain
from api.usecase.file.file import FileUseCase


class TestFileUseCase:
    @pytest.fixture
    def setup(self):
        self.file_usecase = FileUseCase()

    def test_convert_markdown(self, setup, monkeypatch):
        """markdown変換のテスト"""
        expected_data = b"tests"

        monkeypatch.setattr(
            "pypandoc.convert_text",
            lambda *args, outputfile=None, **kwargs: io.BytesIO().write(expected_data),
        )
        monkeypatch.setattr("builtins.open", mock_open(read_data=expected_data))
        monkeypatch.setattr("os.remove", Mock(return_value=None))

        stream = self.file_usecase.convert_markdown_and_create_stream(
            file_domain.Content(root="# test"), file_domain.FileExtension.DOCX
        )
        chunks = list(stream)

        assert b"".join(chunks) == expected_data

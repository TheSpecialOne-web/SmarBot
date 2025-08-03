from abc import ABC, abstractmethod
import os
from typing import Generator
from uuid import uuid4

import pypandoc

from api.domain.models import file as domain
from api.libs.exceptions import BadRequest
from api.libs.file import markdown_to_excel

FileStreamOutput = Generator[bytes, None, None]
CHUNK_SIZE = 1024


class IFileUseCase(ABC):
    @abstractmethod
    def convert_markdown_and_create_stream(
        self, content: domain.Content, extension: domain.FileExtension
    ) -> FileStreamOutput:
        pass


class FileUseCase(IFileUseCase):
    def convert_markdown_and_create_stream(
        self, content: domain.Content, extension: domain.FileExtension
    ) -> FileStreamOutput:
        output_filename = f"conversation-{uuid4()}.{extension.value}"

        content.remove_citations()

        if extension == domain.FileExtension.DOCX:
            pypandoc.convert_text(
                content.root,
                to=extension.value,
                format="md",
                outputfile=output_filename,
                # How to change docx style: reference.docxを開く -> スタイルウィンドウ -> 変更したいスタイルを選択 -> スタイルの変更
                extra_args=["--reference-doc=pandoc/reference.docx"],
                sandbox=True,  # for security
            )
        elif extension == domain.FileExtension.XLSX:
            content.remove_bold()
            try:
                markdown_to_excel(content.root, output_filename)
            except ValueError as e:
                raise BadRequest(str(e))
        else:
            raise BadRequest("サポートされていない拡張子です。")

        try:
            with open(output_filename, "rb") as f:
                while chunk := f.read(CHUNK_SIZE):
                    yield chunk
        finally:
            os.remove(output_filename)

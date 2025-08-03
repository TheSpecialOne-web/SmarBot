from io import BytesIO
from typing import Tuple

from pypdf import PdfReader, PdfWriter

from api.domain.models.attachment import BlobContent
from api.libs.exceptions import BadRequest


def split_pdf_at_page(blob_content: BlobContent, split_page: int) -> Tuple[BlobContent, BlobContent]:
    pdf_stream = BytesIO(blob_content.root)
    try:
        pdf_reader = PdfReader(pdf_stream)

        # 前半部分の作成
        first_writer = PdfWriter()
        for page_num in range(split_page):
            first_writer.add_page(pdf_reader.pages[page_num])

        with BytesIO() as first_bytes:
            first_writer.write(first_bytes)
            first_content = BlobContent(root=first_bytes.getvalue())

        # 後半部分の作成
        second_writer = PdfWriter()
        for page_num in range(split_page, len(pdf_reader.pages)):
            second_writer.add_page(pdf_reader.pages[page_num])

        with BytesIO() as second_bytes:
            second_writer.write(second_bytes)
            second_content = BlobContent(root=second_bytes.getvalue())

        return first_content, second_content
    except Exception:
        raise BadRequest("PDFファイルの分割に失敗しました。")
    finally:
        pdf_stream.close()

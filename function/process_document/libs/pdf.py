from io import BytesIO

import pdfplumber


def parse_pdf_by_pypdf(bytes_stream: BytesIO) -> str:
    with pdfplumber.open(bytes_stream) as pdf:
        page_text = " ".join(page.extract_text() or "" for page in pdf.pages)
    return page_text

import html
from io import BytesIO

from azure.ai.documentintelligence.models import AnalyzeResult
from azure.ai.formrecognizer import DocumentTable
from azure.core.exceptions import ServiceRequestError
from azure.core.polling import LROPoller
from bs4 import BeautifulSoup
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from libs.logging import get_logger

from ..types import Table
from .client import get_form_recognizer

logger = get_logger(__name__)


def convert_table_to_html(table: DocumentTable) -> str:
    try:
        soup = BeautifulSoup("", "html.parser")
        table_soup = soup.new_tag("table")
        rows = [
            sorted([cell for cell in table.cells if cell.row_index == i], key=lambda cell: cell.column_index)
            for i in range(table.row_count)
        ]
        for row_cells in rows:
            tr_tag = soup.new_tag("tr")
            table_soup.append(tr_tag)
            for cell in row_cells:
                attrs: dict[str, str] = {}
                if cell.column_span and cell.column_span > 1:
                    attrs["colSpan"] = str(cell.column_span)
                if cell.row_span and cell.row_span > 1:
                    attrs["rowSpan"] = str(cell.row_span)

                if cell.kind == "columnHeader" or cell.kind == "rowHeader":
                    new_tag = soup.new_tag("th", attrs=attrs)
                else:
                    new_tag = soup.new_tag("td", attrs=attrs)
                new_tag.append(html.escape(cell.content))
                tr_tag.append(new_tag)
            table_soup.append(tr_tag)
        return table_soup.prettify() + "\n"
    finally:
        soup.decompose()


@retry(wait=wait_exponential(), stop=stop_after_attempt(3), reraise=True)
def _get_poller_result(poller: LROPoller[AnalyzeResult]):
    return poller.result()


@retry(
    retry=retry_if_exception_type((ServiceRequestError)),
    wait=wait_exponential(),
    stop=stop_after_attempt(3),
    reraise=True,
)
def parse_pdf_by_document_intelligence(bytes_stream: BytesIO) -> str:
    form_recognizer_client = get_form_recognizer()
    poller = form_recognizer_client.begin_analyze_document("prebuilt-layout", document=bytes_stream)
    form_recognizer_results = _get_poller_result(poller)

    tables_on_page = list(form_recognizer_results.tables)
    # mark all positions of the table spans in the page
    page_offset = form_recognizer_results.pages[0].spans[0].offset
    page_length = form_recognizer_results.pages[0].spans[0].length

    # ページ内に存在する全文字に対してテーブルの一部なのかを入れる配列(-1は文章、1以上はテーブル)
    chars_in_page = [-1] * page_length
    for table_id, table in enumerate(tables_on_page):
        for span in table.spans:
            # replace all table spans with "table_id" in table_chars array
            for i in range(span.length):
                idx = span.offset - page_offset + i
                if idx >= 0 and idx < page_length:
                    chars_in_page[idx] = table_id

    # build page text by replacing charcters in table spans with table html
    page_text = ""
    added_tables = set()
    for idx, table_id in enumerate(chars_in_page):
        if table_id == -1:
            page_text += form_recognizer_results.content[page_offset + idx]
        elif table_id not in added_tables:
            try:
                table_text = "\n".join(Table.from_document_intelligence_table(tables_on_page[table_id]).to_chunks())
            except Exception as e:
                logger.warning(
                    f"Failed to convert document intelligence table to table class: {tables_on_page[table_id]}",
                    exc_info=e,
                )
                table_text = convert_table_to_html(tables_on_page[table_id])
            page_text += table_text
            added_tables.add(table_id)
    return page_text

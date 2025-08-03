import html
from io import BytesIO
import os
from typing import Tuple

from azure.ai.formrecognizer import DocumentAnalysisClient, DocumentTable
from azure.identity import DefaultAzureCredential
from bs4 import BeautifulSoup

from api.domain.models.attachment.content import BlobContent, Content
from api.domain.models.metering.quantity import Quantity
from api.domain.services.document_intelligence.document_intelligence import (
    IDocumentIntelligenceService,
)
from api.libs.logging import get_logger
from api.libs.table import Table

logger = get_logger()

FORM_RECOGNIZER_SERVICE = os.environ.get("FORM_RECOGNIZER_SERVICE") or "myformrecognizerservice"


class DocumentIntelligenceService(IDocumentIntelligenceService):
    def __init__(self, azure_credential: DefaultAzureCredential):
        self.client = DocumentAnalysisClient(
            endpoint=f"https://{FORM_RECOGNIZER_SERVICE}.cognitiveservices.azure.com/",
            credential=azure_credential,
        )

    def _convert_table_to_html(self, table: DocumentTable) -> str:
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

    def parse_pdf(self, bytes: BlobContent) -> Tuple[Content, Quantity]:
        with BytesIO(bytes.root) as stream:
            poller = self.client.begin_analyze_document("prebuilt-layout", document=stream)
            document_intelligence_results = poller.result()
        result_pages = document_intelligence_results.pages
        page_count = Quantity(root=len(result_pages))
        content = ""
        for page_num, page in enumerate(result_pages):
            tables_on_page = (
                [
                    table_di
                    for table_di in document_intelligence_results.tables
                    if table_di.bounding_regions is not None
                    and table_di.bounding_regions[0].page_number == page_num + 1
                ]
                if document_intelligence_results.tables is not None
                else []
            )
            # mark all positions of the table spans in the page
            page_offset = page.spans[0].offset
            page_length = page.spans[0].length
            table_chars = [-1] * page_length
            for table_id, table_di in enumerate(tables_on_page):
                for span in table_di.spans:
                    # replace all table spans with "table_id" in table_chars array
                    for i in range(span.length):
                        idx = span.offset - page_offset + i
                        if idx >= 0 and idx < page_length:
                            table_chars[idx] = table_id
            # build page text by replacing charcters in table spans with table html
            added_tables = set()
            for idx, table_id in enumerate(table_chars):
                if table_id == -1:
                    content += document_intelligence_results.content[page_offset + idx]
                elif table_id not in added_tables:
                    try:
                        table_text = Table.from_document_intelligence_table(tables_on_page[table_id]).to_text()
                    except Exception as e:
                        logger.warning(
                            f"Failed to convert document intelligence table to table class: {tables_on_page[table_id]}",
                            exc_info=e,
                        )
                        table_text = self._convert_table_to_html(tables_on_page[table_id])
                    content += table_text
                    added_tables.add(table_id)
            content += "\n"
        return Content(root=content), page_count

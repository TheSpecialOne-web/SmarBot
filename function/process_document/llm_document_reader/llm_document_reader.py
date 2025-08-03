import html
from io import BytesIO

from azure.ai.documentintelligence.models import DocumentAnalysisFeature, DocumentTable
from azure.core.exceptions import ServiceRequestError
from bs4 import BeautifulSoup
import cv2
import fitz
import numpy as np
from PIL import Image
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from libs.logging import get_logger

from ..types import Table
from .client import get_client_settings, get_form_recognizer, init_vertexai
from .image_describer import ImageData, ImageDescriber, ImageDescriberInput

logger = get_logger(__name__)

MINUMUN_IMAGE_SIZE = 4
DPI = 150
MAX_IMAGE_COUNT = 3

IMAGE_DESCRIBER_MODEL = "gemini-1.5-flash-002"
IMAGE_DESCRIBER_PLATFORM = "gcp"


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


@retry(
    retry=retry_if_exception_type((ServiceRequestError)),
    wait=wait_exponential(),
    stop=stop_after_attempt(3),
    reraise=True,
)
def parse_pdf_by_llm_document_reader(bytes_stream: BytesIO) -> str:
    client = get_form_recognizer()
    init_vertexai()
    poller = client.begin_analyze_document(
        "prebuilt-layout",
        analyze_request=bytes_stream,
        locale="ja-JP",
        features=[DocumentAnalysisFeature.OCR_HIGH_RESOLUTION],
        content_type="application/octet-stream",
    )

    ocr_result = poller.result()

    pages = fitz.open(stream=bytes_stream.getvalue(), filetype="pdf")
    page = pages[0]
    pix = page.get_pixmap(dpi=DPI)
    page_image = np.array(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
    page_image = np.array(cv2.cvtColor(page_image, cv2.COLOR_RGB2BGR))

    image_info_list = []

    if ocr_result.figures:
        for figure in ocr_result.figures:
            image_info = {}
            image_info["spans"] = figure.spans

            # 画像が複数領域を持っている場合、合体した一番大きい領域で切り抜く
            # 左上
            polygon_x1 = min(region.polygon[0] for region in figure.bounding_regions)
            polygon_y1 = min(region.polygon[1] for region in figure.bounding_regions)
            # 右上
            polygon_x2 = max(region.polygon[2] for region in figure.bounding_regions)
            polygon_y2 = min(region.polygon[3] for region in figure.bounding_regions)
            # 右下
            polygon_x3 = max(region.polygon[4] for region in figure.bounding_regions)
            polygon_y3 = max(region.polygon[5] for region in figure.bounding_regions)
            # 左下
            polygon_x4 = min(region.polygon[6] for region in figure.bounding_regions)
            polygon_y4 = max(region.polygon[7] for region in figure.bounding_regions)

            image_info["polygon"] = [
                polygon_x1,
                polygon_y1,
                polygon_x2,
                polygon_y2,
                polygon_x3,
                polygon_y3,
                polygon_x4,
                polygon_y4,
            ]

            image_info["area"] = (max(image_info["polygon"][0::2]) - min(image_info["polygon"][0::2])) * (
                max(image_info["polygon"][1::2]) - min(image_info["polygon"][1::2])
            )

            cropped_image = page_image[
                int(image_info["polygon"][1] * DPI) : int(image_info["polygon"][5] * DPI),
                int(image_info["polygon"][0] * DPI) : int(image_info["polygon"][4] * DPI),
            ]

            image_info["image_data"] = cropped_image

            paragraphs_in_image = []
            paragraphs_around_image = []

            if figure.elements:
                for i, element in enumerate(figure.elements):
                    # elementは"paragraphs/3"みたいな感じ
                    idx_paragraph = int(element.split("/")[-1])
                    paragraphs_in_image.append(ocr_result.paragraphs[idx_paragraph].content)

                    # 画像直前の文
                    if i == 0 and idx_paragraph > 0:
                        paragraphs_around_image.append(ocr_result.paragraphs[idx_paragraph - 1].content)
                    # 画像直後の文
                    if i == len(figure.elements) - 1 and idx_paragraph < len(ocr_result.paragraphs) - 1:
                        paragraphs_around_image.append(ocr_result.paragraphs[idx_paragraph + 1].content)

            image_info["text_included"] = [remove_selected_unselected(text) for text in paragraphs_in_image]
            image_info["text_around"] = [remove_selected_unselected(text) for text in paragraphs_around_image]
            image_info_list.append(image_info)

    # 画像内に文字がないものは落とす
    image_info_list = [image_info for image_info in image_info_list if len(image_info["text_included"]) > 0]
    # 面積の小さいものを落とす
    image_info_list = [image_info for image_info in image_info_list if image_info["area"] > MINUMUN_IMAGE_SIZE]
    # 大きい方からMAX_IMAGE_COUNTだけとってくる
    image_info_list.sort(key=lambda image_info: image_info["area"], reverse=True)
    image_info_list = image_info_list[:MAX_IMAGE_COUNT]

    # ページ内のすべてのテーブルと画像の位置をマーク
    page_offset = ocr_result.pages[0].spans[0].offset
    num_char = ocr_result.pages[0].spans[0].length

    # ページ内に存在する全文字に対してテーブルの一部なのかを入れる(-1は文章、0以上はテーブル)
    chars_in_page_table: list[int] = [-1] * num_char
    for table_id, table in enumerate(ocr_result.tables):
        for span in table.spans:
            for i in range(span.length):
                idx = span.offset - page_offset + i
                if 0 <= idx < num_char:
                    chars_in_page_table[idx] = table_id

    # ページ内に存在する全文字に対して画像の一部なのかを入れる(-1は文章、0以上は画像)
    chars_in_page_figure: list[int] = [-1] * num_char
    for figure_id, image_info in enumerate(image_info_list):
        for span in image_info["spans"]:
            for i in range(span.length):
                idx = span.offset - page_offset + i
                if 0 <= idx < num_char:
                    chars_in_page_figure[idx] = figure_id

    # テーブルスパン内の文字をテーブルHTMLに置き換え、画像スパン内の文字には画像説明を呼び出してページテキストを構築
    page_text = ""
    added_tables: set[int] = set()
    added_figures: set[int] = set()
    for idx, (table_id, figure_id) in enumerate(zip(chars_in_page_table, chars_in_page_figure)):
        if table_id in added_tables or figure_id in added_figures:
            continue
        if table_id != -1:
            try:
                table_text = "\n".join(Table.from_document_intelligence_table(ocr_result.tables[table_id]).to_chunks())
            except Exception:
                logger.warning(f"Failed to convert docx table to table class: {ocr_result.tables[table_id]}")
                table_text = convert_table_to_html(ocr_result.tables[table_id])
            page_text += table_text
            added_tables.add(table_id)
            continue

        if figure_id != -1:
            image_describer = ImageDescriber(
                model=IMAGE_DESCRIBER_MODEL,
                client_settings=get_client_settings(),
                llm_settings={"temperature": 0.2, "max_tokens": 1000},
                verbose=False,
                platform=IMAGE_DESCRIBER_PLATFORM,
                stream_verbose=False,
                silent_list=[],
            )

            text_in_image = list(image_info_list[figure_id]["text_included"])
            text_around_image = list(image_info_list[figure_id]["text_around"])

            image_describer_input = ImageDescriberInput(
                image_data=ImageData(root=image_info_list[figure_id]["image_data"]),
                text_in_image=text_in_image,
                text_around_image=text_around_image,
            )

            try:
                image_description = image_describer(image_describer_input).description
            except Exception as e:
                logger.warning(f"failed to describe image: {e}")
                image_description = ""

            page_text += image_description
            added_figures.add(figure_id)
            continue

        # 画像や表に含まれない通常の文字のとき
        page_text += ocr_result.content[page_offset + idx]
    return remove_selected_unselected(page_text)


def remove_selected_unselected(text: str) -> str:
    cleaned_text = text.replace(":selected:", "").replace(":unselected:", "")
    return cleaned_text

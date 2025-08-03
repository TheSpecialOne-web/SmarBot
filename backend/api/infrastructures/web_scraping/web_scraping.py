import re

from bs4 import BeautifulSoup
import requests

from api.domain.models.data_point import (
    BlobPath,
    ChunkName,
    CiteNumber,
    Content,
    DataPoint,
    PageNumber,
    Type,
    Url,
)
from api.domain.services.web_scraping import IWebScrapingService

MAX_URL_COUNT = 3


class WebScrapingService(IWebScrapingService):
    def find_url_from_text(self, text: str) -> list[str]:
        urls = re.findall(r"https?://\S+", text)
        return urls

    def web_search_from_url(self, urls: list[str]) -> list[DataPoint]:
        data_points: list[DataPoint] = []
        for url in urls[:MAX_URL_COUNT]:
            r = requests.get(url)
            try:
                soup = BeautifulSoup(r.text, "html.parser")
                title_found = soup.find("title")
                title = soup.get_text() if title_found else url
                content_found = soup.find("body")
            finally:
                soup.decompose()
            content = (
                "Webサイトの情報の取得に失敗しました。"
                if not content_found or not content_found.get_text()
                else content_found.get_text()
            )

            data_points.append(
                DataPoint(
                    content=Content(root=content),
                    cite_number=CiteNumber(root=0),
                    page_number=PageNumber(root=0),
                    chunk_name=ChunkName(root=title),
                    blob_path=BlobPath(root=""),
                    type=Type.WEB,
                    url=Url(root=url),
                    additional_info=None,
                    document_id=None,
                )
            )
        return data_points

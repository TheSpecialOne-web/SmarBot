import json
import os
import urllib.parse

import requests

from api.domain.models.data_point import (
    BlobPath,
    ChunkName,
    Content,
    DataPointWithoutCiteNumber,
    PageNumber,
    Type,
    Url,
)
from api.domain.models.query import Queries
from api.domain.services.bing_search import IBingSearchService

BING_SUBSCRIPTION_KEY = os.environ.get("BING_SUBSCRIPTION_KEY")
BING_CUSTOM_CONFIG_ID = os.environ.get("BING_CUSTOM_CONFIG_ID")

# Max URL length for Bing API is 2048
# https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/reference/endpoints#endpoints
MAX_URL_LENGTH = 2048


class BingSearchService(IBingSearchService):
    def search_web_documents(self, queries: Queries) -> list[DataPointWithoutCiteNumber]:
        if not BING_SUBSCRIPTION_KEY:
            raise Exception("BING_SUBSCRIPTION_KEY is not set")
        if not BING_CUSTOM_CONFIG_ID:
            raise Exception("BING_CUSTOM_CONFIG_ID is not set")

        q = queries.to_string(delimiter="+")
        if not q:
            return []

        url = f"https://api.bing.microsoft.com/v7.0/custom/search?customconfig={BING_CUSTOM_CONFIG_ID}&q={q}"
        encoded_url = urllib.parse.quote(url)
        if len(encoded_url) > MAX_URL_LENGTH:
            url = urllib.parse.unquote(encoded_url[:MAX_URL_LENGTH])

        r = requests.get(url, headers={"Ocp-Apim-Subscription-Key": BING_SUBSCRIPTION_KEY})

        if r.status_code != 200:
            raise Exception(f"Failed to search web documents. code: {r.status_code}, detail: {r.text}")
        try:
            result = json.loads(r.text)
        except json.JSONDecodeError:
            # Web検索結果が空の場合は空リストを返してチャットを継続する
            return []

        data_points: list[DataPointWithoutCiteNumber] = []
        try:
            for page_result in result["webPages"]["value"]:
                content = page_result["snippet"]
                url = page_result["url"]
                data_points.append(
                    DataPointWithoutCiteNumber(
                        content=Content(root=content),
                        page_number=PageNumber(root=0),
                        chunk_name=ChunkName(root=page_result["name"]),
                        blob_path=BlobPath(root=""),
                        type=Type.WEB,
                        url=Url(root=url),
                        additional_info=None,
                        document_id=None,
                    )
                )
        except KeyError:
            return []

        return data_points

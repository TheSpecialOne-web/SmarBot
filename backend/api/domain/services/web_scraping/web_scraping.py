from abc import ABC, abstractmethod

from api.domain.models.data_point import DataPoint


class IWebScrapingService(ABC):
    @abstractmethod
    def find_url_from_text(self, text: str) -> list[str]:
        pass

    @abstractmethod
    def web_search_from_url(self, urls: list[str]) -> list[DataPoint]:
        pass

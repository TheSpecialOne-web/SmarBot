from abc import ABC, abstractmethod

from api.domain.models.data_point import DataPointWithoutCiteNumber
from api.domain.models.query import Queries


class IBingSearchService(ABC):
    @abstractmethod
    def search_web_documents(self, queries: Queries) -> list[DataPointWithoutCiteNumber]:
        pass

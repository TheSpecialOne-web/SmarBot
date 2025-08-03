from abc import ABC, abstractmethod
from typing import Tuple

from api.domain.models.metering.quantity import Quantity

from ...models.attachment.content import BlobContent, Content


class IDocumentIntelligenceService(ABC):
    @abstractmethod
    def parse_pdf(self, bytes: BlobContent) -> Tuple[Content, Quantity]:
        pass

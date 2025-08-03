from abc import ABC, abstractmethod
from typing import Tuple

from api.domain.models.metering.quantity import Quantity

from ...models.attachment.content import BlobContent, Content


class IAiVisionService(ABC):
    @abstractmethod
    def parse_pdf_by_ai_vision(self, bytes: BlobContent) -> Tuple[Content, Quantity]:
        pass

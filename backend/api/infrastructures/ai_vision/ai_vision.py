from io import BytesIO
import os
import time
from typing import Final

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.identity import DefaultAzureCredential
from msrest.authentication import BasicTokenAuthentication

from api.domain.models.attachment.content import BlobContent, Content
from api.domain.models.metering.quantity import Quantity
from api.domain.services.ai_vision.ai_vision import IAiVisionService

COMPUTER_VISION_ENDPOINT = os.environ.get("COMPUTER_VISION_ENDPOINT")

MAX_POLLING_SEC: Final[int] = 60


class AiVisionService(IAiVisionService):
    def __init__(self, azure_credential: DefaultAzureCredential) -> None:
        self.azure_credential = azure_credential

    def _get_client(self) -> ComputerVisionClient:
        access_token = self.azure_credential.get_token("https://cognitiveservices.azure.com/.default")
        return ComputerVisionClient(
            endpoint=COMPUTER_VISION_ENDPOINT,
            credentials=BasicTokenAuthentication({"access_token": access_token.token}),
        )

    def parse_pdf_by_ai_vision(self, bytes: BlobContent) -> tuple[Content, Quantity]:
        client = self._get_client()
        with BytesIO(bytes.root) as pdf_stream:
            read_response = client.read_in_stream(pdf_stream, raw=True)

        read_operation_location = read_response.headers["Operation-Location"]
        operation_id = read_operation_location.split("/")[-1]

        for _ in range(MAX_POLLING_SEC):
            read_result = client.get_read_result(operation_id)
            if read_result.status not in ["notStarted", "running"]:
                break
            time.sleep(1)
        else:
            raise Exception(f"Timeout: AI Vision operation did not complete within {MAX_POLLING_SEC} seconds.")

        content = ""
        if read_result.status == OperationStatusCodes.succeeded:
            for text_result in read_result.analyze_result.read_results:
                for line in text_result.lines:
                    content += line.text
        return Content(root=content), Quantity(root=len(read_result.analyze_result.read_results))

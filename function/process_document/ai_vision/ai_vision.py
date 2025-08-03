from io import BytesIO
import time
from typing import Final

from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes

from .client import get_ai_vision_client

MAX_POLLING_SEC: Final[int] = 180


def parse_pdf_by_azure_ai_vision(bytes_stream: BytesIO) -> str:
    ai_vision_client = get_ai_vision_client()

    read_response = ai_vision_client.read_in_stream(bytes_stream, raw=True)

    read_operation_location = read_response.headers["Operation-Location"]
    operation_id = read_operation_location.split("/")[-1]

    for _ in range(MAX_POLLING_SEC):
        read_result = ai_vision_client.get_read_result(operation_id)
        if read_result.status not in ["notStarted", "running"]:
            break
        time.sleep(1)
    else:
        raise Exception(f"Timeout: AI Vision operation did not complete within {MAX_POLLING_SEC} seconds.")

    page_texts = ""
    if read_result.status == OperationStatusCodes.succeeded:
        for text_result in read_result.analyze_result.read_results:
            for line in text_result.lines:
                page_texts += line.text
    return page_texts

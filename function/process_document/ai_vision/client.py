import os

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.identity import DefaultAzureCredential
from msrest.authentication import BasicTokenAuthentication

COMPUTER_VISION_ENDPOINT = os.environ.get("COMPUTER_VISION_ENDPOINT")

azure_credential = DefaultAzureCredential()


def get_ai_vision_client():
    access_token = azure_credential.get_token("https://cognitiveservices.azure.com/.default")
    return ComputerVisionClient(
        endpoint=COMPUTER_VISION_ENDPOINT,
        credentials=BasicTokenAuthentication({"access_token": access_token.token}),
    )

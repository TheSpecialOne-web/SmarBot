import os

from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.identity import DefaultAzureCredential

FORM_RECOGNIZER_SERVICE = os.environ.get("FORM_RECOGNIZER_SERVICE") or "myformrecognizerservice"

azure_credential = DefaultAzureCredential()


def get_form_recognizer():
    return DocumentAnalysisClient(
        endpoint=f"https://{FORM_RECOGNIZER_SERVICE}.cognitiveservices.azure.com/",
        credential=azure_credential,
    )

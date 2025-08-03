from enum import Enum


class Platform(str, Enum):
    AZURE = "azure"
    GCP = "gcp"
    OPENAI = "openai"

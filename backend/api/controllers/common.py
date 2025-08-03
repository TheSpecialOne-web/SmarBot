from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict


class CustomBaseModel(BaseModel):
    model_config = ConfigDict(
        protected_namespaces=(
            "model_family_",
            "model_families_",
        )
    )


CSV_RESPONSE = {
    "content": {
        "text/csv": {
            "schema": {
                "type": "string",
                "format": "binary",
            },
        },
    },
}

OCTET_STREAM_RESPONSE = {
    "content": {
        "application/octet-stream": {
            "schema": {
                "type": "string",
                "format": "binary",
            },
        },
    },
}


class CSVResponse(StreamingResponse):
    media_type = "text/csv"


class OctetStreamResponse(StreamingResponse):
    media_type = "application/octet-stream"


ALLOWED_MIME_TYPES = [
    "application/pdf",
    "application/octet-stream",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain",
]

ADDITIONAL_ALLOWED_MIME_TYPES = [
    "application/msword",
    "application/vnd.ms-excel",
    "application/vnd.ms-powerpoint",
    "application/vnd.ms-excel.sheet.macroenabled.12",
    "application/vnd.fujifilm.fb.docuworks",
]


def get_allowed_mime_types(flag: bool) -> list[str]:
    mime_types = ALLOWED_MIME_TYPES
    if flag:
        mime_types.extend(ADDITIONAL_ALLOWED_MIME_TYPES)
    return mime_types

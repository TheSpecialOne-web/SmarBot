from enum import Enum
import re
from re import Pattern

from pydantic import BaseModel, StrictBool, StrictStr


class SensitiveContentType(str, Enum):
    PHONE_NUMBER = "phone_number"
    EMAIL = "email"
    POSTAL_CODE = "postal_code"
    MY_NUMBER = "my_number"
    CREDIT_CARD = "credit_card"

    @classmethod
    def to_list(cls) -> list[str]:
        return [member.value for member in cls]

    @classmethod
    def get_pattern(cls, content_type: "SensitiveContentType") -> Pattern[str] | None:
        patterns = {
            cls.PHONE_NUMBER: re.compile(
                r"(?<![\d-])(?:(\d{4}-\d{3}-\d{3}|\d{3}-\d{3}-\d{4}|\d{3}-\d{4}-\d{4}|\d{4}-\d{2}-\d{4}|\d{2}-\d{4}-\d{4})|\d{11}|\d{10})(?![\d-])"
            ),
            cls.EMAIL: re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}"),
            cls.POSTAL_CODE: re.compile(r"(?<![\d-])[0-9]{3}-[0-9]{4}(?![\d-])"),
            cls.MY_NUMBER: re.compile(r"(?<![\d-])(\d{4}-\d{4}-\d{4}|\d{12})(?![\d-])"),
            cls.CREDIT_CARD: re.compile(r"\d{4}-\d{4}-\d{4}-\d{4}|\d{16}"),
        }
        return patterns.get(content_type)

    @classmethod
    def from_value(cls, value: str) -> "SensitiveContentType | None":
        try:
            return cls(value)
        except ValueError:
            return None


class SensitiveContent(BaseModel):
    type: SensitiveContentType
    content: StrictStr


class Validation(BaseModel):
    is_valid: StrictBool
    sensitive_contents: list[SensitiveContent]

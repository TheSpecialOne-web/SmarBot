from enum import Enum


class Status(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "processing"
    FAILED = "failed"

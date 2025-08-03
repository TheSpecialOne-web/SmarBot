from enum import Enum


class Status(str, Enum):
    PROCESSING = "processing"
    ACTIVE = "active"
    DELETED = "deleted"
    ERROR = "error"

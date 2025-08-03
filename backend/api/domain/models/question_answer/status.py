from enum import Enum


class Status(str, Enum):
    PENDING = "pending"
    INDEXED = "indexed"
    FAILED = "failed"
    OVERWRITING = "overwriting"

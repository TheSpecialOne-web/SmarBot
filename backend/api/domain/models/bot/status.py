from enum import Enum


class Status(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETING = "deleting"
    BASIC_AI_DELETED = "basic_ai_deleted"

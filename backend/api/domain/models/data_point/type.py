from enum import Enum


class Type(str, Enum):
    INTERNAL = "internal"
    WEB = "web"
    QUESTION_ANSWER = "question_answer"

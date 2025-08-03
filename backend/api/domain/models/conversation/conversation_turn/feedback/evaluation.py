from enum import Enum


class Evaluation(str, Enum):
    """
    フィードバックを表すEnum
    """

    GOOD = "good"
    BAD = "bad"

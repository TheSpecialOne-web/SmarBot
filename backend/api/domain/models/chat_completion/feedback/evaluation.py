from enum import Enum


class Evaluation(str, Enum):
    """
    評価を表すEnum
    """

    GOOD = "good"
    BAD = "bad"

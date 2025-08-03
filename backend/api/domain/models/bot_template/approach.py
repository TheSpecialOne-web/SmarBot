from enum import Enum


class Approach(str, Enum):
    """
    アプローチを表すEnum
    """

    NEOLLM = "neollm"
    CHAT_GPT_DEFAULT = "chat_gpt_default"
    CUSTOM_GPT = "custom_gpt"
    URSA = "ursa"

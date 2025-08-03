from enum import Enum


class Approach(str, Enum):
    """
    アプローチを表すEnum
    """

    NEOLLM = "neollm"
    CHAT_GPT_DEFAULT = "chat_gpt_default"
    CUSTOM_GPT = "custom_gpt"
    TEXT_2_IMAGE = "text_2_image"
    URSA = "ursa"

    def is_basic_ai(self) -> bool:
        return self in {self.CHAT_GPT_DEFAULT, self.TEXT_2_IMAGE}

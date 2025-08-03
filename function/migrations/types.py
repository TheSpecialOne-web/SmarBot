from enum import Enum


class ModelName(str, Enum):
    GPT_35_TURBO = "gpt-3.5-turbo"
    GPT_35_TURBO_16K = "gpt-3.5-turbo-16k"
    GPT_4 = "gpt-4"
    GPT_35_TURBO_1106 = "gpt-3.5-turbo-1106"
    GPT_4_TURBO_1106 = "gpt-4-turbo-1106"
    GPT_4_TURBO_2024_04_09 = "gpt-4-turbo-2024-04-09"
    GPT_4O_2024_05_13 = "gpt-4o-2024-05-13"
    GPT_4O_MINI_2024_07_18 = "gpt-4o-mini-2024-07-18"
    GPT_4_TURBO_2024_04_09_OPENAI = "gpt-4-turbo-2024-04-09-openai"
    GPT_4O_2024_05_13_OPENAI = "gpt-4o-2024-05-13-openai"
    CLAUDE_3_OPUS_20240229 = "claude-3-opus@20240229"
    CLAUDE_3_SONNET_20240229 = "claude-3-sonnet@20240229"
    CLAUDE_3_HAIKU_20240307 = "claude-3-haiku@20240307"
    CLAUDE_35_SONNET_20240620 = "claude-3-5-sonnet@20240620"
    GEMINI_10_PRO = "gemini-1.0-pro"
    GEMINI_15_PRO_PREVIEW_0409 = "gemini-1.5-pro-preview-0409"
    GEMINI_15_PRO_001 = "gemini-1.5-pro-001"
    GEMINI_15_FLASH_001 = "gemini-1.5-flash-001"

    def to_model_family(self):
        if self in {ModelName.GPT_35_TURBO, ModelName.GPT_35_TURBO_16K, ModelName.GPT_35_TURBO_1106}:
            return ModelFamily.GPT_35_TURBO

        if self == ModelName.GPT_4:
            return ModelFamily.GPT_4

        if self in {
            ModelName.GPT_4_TURBO_1106,
            ModelName.GPT_4_TURBO_2024_04_09,
            ModelName.GPT_4_TURBO_2024_04_09_OPENAI,
        }:
            return ModelFamily.GPT_4_TURBO

        if self in {ModelName.GPT_4O_2024_05_13, ModelName.GPT_4O_2024_05_13_OPENAI}:
            return ModelFamily.GPT_4O

        if self == ModelName.GPT_4O_MINI_2024_07_18:
            return ModelFamily.GPT_4O_MINI

        if self == ModelName.CLAUDE_3_OPUS_20240229:
            return ModelFamily.CLAUDE_3_OPUS

        if self == ModelName.CLAUDE_3_SONNET_20240229:
            return ModelFamily.CLAUDE_3_SONNET

        if self == ModelName.CLAUDE_3_HAIKU_20240307:
            return ModelFamily.CLAUDE_3_HAIKU

        if self == ModelName.CLAUDE_35_SONNET_20240620:
            return ModelFamily.CLAUDE_35_SONNET

        if self == ModelName.GEMINI_10_PRO:
            return ModelFamily.GEMINI_10_PRO

        if self in {ModelName.GEMINI_15_PRO_PREVIEW_0409, ModelName.GEMINI_15_PRO_001}:
            return ModelFamily.GEMINI_15_PRO

        if self == ModelName.GEMINI_15_FLASH_001:
            return ModelFamily.GEMINI_15_FLASH

        raise Exception(f"Failed to get model family: {self}")


class ModelFamily(str, Enum):
    GPT_35_TURBO = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    CLAUDE_3_OPUS = "claude-3-opus"
    CLAUDE_3_SONNET = "claude-3-sonnet"
    CLAUDE_3_HAIKU = "claude-3-haiku"
    CLAUDE_35_SONNET = "claude-3.5-sonnet"
    GEMINI_10_PRO = "gemini-1.0-pro"
    GEMINI_15_PRO = "gemini-1.5-pro"
    GEMINI_15_FLASH = "gemini-1.5-flash"


class Text2ImageModelFamily(str, Enum):
    DALL_E_3 = "dall-e-3"


class Text2ImageModel(str, Enum):
    DALL_E_3 = "dall-e-3"

    def to_model_family(self):
        if self == Text2ImageModel.DALL_E_3:
            return Text2ImageModelFamily.DALL_E_3
        raise Exception(f"failed to get image generator model family: {self}")

from enum import Enum
from typing import Literal

from .allow_foreign_region import AllowForeignRegion
from .platform import Platform


class ModelName(str, Enum):
    GPT_35_TURBO = "gpt-3.5-turbo"
    GPT_35_TURBO_16K = "gpt-3.5-turbo-16k"
    GPT_35_TURBO_1106 = "gpt-3.5-turbo-1106"
    GPT_4 = "gpt-4"
    GPT_4_TURBO_1106 = "gpt-4-turbo-1106"
    GPT_4_TURBO_2024_04_09 = "gpt-4-turbo-2024-04-09"
    GPT_4O_2024_05_13 = "gpt-4o-2024-05-13"
    GPT_4O_2024_08_06 = "gpt-4o-2024-08-06"
    GPT_4O_MINI_2024_07_18 = "gpt-4o-mini-2024-07-18"
    O1_PREVIEW_20240912 = "o1-preview-2024-09-12"
    O1_MINI_20240912 = "o1-mini-2024-09-12"
    CLAUDE_3_OPUS_20240229 = "claude-3-opus@20240229"
    CLAUDE_3_SONNET_20240229 = "claude-3-sonnet@20240229"
    CLAUDE_3_HAIKU_20240307 = "claude-3-haiku@20240307"
    CLAUDE_35_SONNET_20240620 = "claude-3-5-sonnet@20240620"
    CLAUDE_35_SONNET_V2_20241022 = "claude-3-5-sonnet-v2@20241022"
    CLAUDE_35_HAIKU_20241022 = "claude-3-5-haiku@20241022"
    GEMINI_10_PRO = "gemini-1.0-pro"
    GEMINI_15_PRO_PREVIEW_0409 = "gemini-1.5-pro-preview-0409"
    GEMINI_15_PRO_001 = "gemini-1.5-pro-001"
    GEMINI_15_PRO_002 = "gemini-1.5-pro-002"
    GEMINI_15_FLASH_001 = "gemini-1.5-flash-001"
    GEMINI_15_FLASH_002 = "gemini-1.5-flash-002"
    GEMINI_20_FLASH_EXP = "gemini-2.0-flash-exp"

    def is_foreign_region(self) -> bool:
        return self in [
            ModelName.GPT_35_TURBO_1106,
            ModelName.GPT_4_TURBO_1106,
            ModelName.CLAUDE_3_OPUS_20240229,
            ModelName.CLAUDE_3_SONNET_20240229,
            ModelName.CLAUDE_3_HAIKU_20240307,
            ModelName.CLAUDE_35_SONNET_20240620,
            ModelName.CLAUDE_35_SONNET_V2_20241022,
            ModelName.CLAUDE_35_HAIKU_20241022,
            ModelName.GPT_4_TURBO_2024_04_09,
            ModelName.GPT_4O_2024_05_13,
            ModelName.GPT_4O_2024_08_06,
            ModelName.GPT_4O_MINI_2024_07_18,
            ModelName.O1_PREVIEW_20240912,
            ModelName.O1_MINI_20240912,
            ModelName.GEMINI_20_FLASH_EXP,
        ]

    def is_gcp_only(self) -> bool:
        return self in [
            ModelName.CLAUDE_3_OPUS_20240229,
            ModelName.CLAUDE_3_SONNET_20240229,
            ModelName.CLAUDE_3_HAIKU_20240307,
            ModelName.CLAUDE_35_SONNET_20240620,
            ModelName.CLAUDE_35_SONNET_V2_20241022,
            ModelName.CLAUDE_35_HAIKU_20241022,
            ModelName.GEMINI_10_PRO,
            ModelName.GEMINI_15_PRO_PREVIEW_0409,
            ModelName.GEMINI_15_PRO_001,
            ModelName.GEMINI_15_PRO_002,
            ModelName.GEMINI_15_FLASH_001,
            ModelName.GEMINI_15_FLASH_002,
            ModelName.GEMINI_20_FLASH_EXP,
        ]

    def is_gpt(self) -> bool:
        return self.value.startswith("gpt") or self.value.startswith("o1")

    def is_o1(self) -> bool:
        return self.value.startswith("o1")

    def is_reasoning_model(self) -> bool:
        return self.is_o1()

    def is_claude(self) -> bool:
        return self.value.startswith("claude")

    def is_gemini(self) -> bool:
        return self.value.startswith("gemini")

    def is_openai_only(self) -> bool:
        return self in []

    def to_model(self) -> str:
        model = self.value
        if model == ModelName.GPT_35_TURBO:
            model = ModelName.GPT_35_TURBO_16K
        return model

    def to_platform(self) -> Platform:
        if self.is_gcp_only():
            return Platform.GCP
        if self.is_openai_only():
            return Platform.OPENAI
        return Platform.AZURE

    def get_token_coefficient(self, is_via_api: bool) -> float:
        return {
            ModelName.GPT_4: 3.0,
            ModelName.GPT_4_TURBO_1106: 1.0,
            ModelName.GPT_4_TURBO_2024_04_09: 1.0,
            ModelName.GPT_4O_2024_05_13: 0.5,
            ModelName.GPT_4O_2024_08_06: 0.5,
            ModelName.GPT_4O_MINI_2024_07_18: 0.2 if is_via_api else 0.0,
            ModelName.GPT_35_TURBO: 0.2,
            ModelName.GPT_35_TURBO_16K: 0.2,
            ModelName.GPT_35_TURBO_1106: 0.2,
            ModelName.O1_PREVIEW_20240912: 5.0,
            ModelName.O1_MINI_20240912: 1.0,
            ModelName.CLAUDE_3_OPUS_20240229: 3.0,
            ModelName.CLAUDE_3_SONNET_20240229: 1.0,
            ModelName.CLAUDE_3_HAIKU_20240307: 0.2,
            ModelName.CLAUDE_35_SONNET_20240620: 1.0,
            ModelName.CLAUDE_35_SONNET_V2_20241022: 1.0,
            ModelName.CLAUDE_35_HAIKU_20241022: 0.5,
            ModelName.GEMINI_10_PRO: 0.2,
            ModelName.GEMINI_15_PRO_PREVIEW_0409: 0.2,
            ModelName.GEMINI_15_PRO_001: 0.5,
            ModelName.GEMINI_15_PRO_002: 0.5,
            ModelName.GEMINI_15_FLASH_001: 0.2,
            ModelName.GEMINI_15_FLASH_002: 0.2,
            ModelName.GEMINI_20_FLASH_EXP: 0.2,
        }[self]


# 優先順位を定義
GPT_35_TURBO_MODEL_NAMES_ORDER = [
    ModelName.GPT_35_TURBO_16K,
    ModelName.GPT_35_TURBO,
]
GPT_4_MODEL_NAMES_ORDER = [
    ModelName.GPT_4,
]
GPT_4_TURBO_MODEL_NAMES_ORDER = [
    ModelName.GPT_4_TURBO_2024_04_09,
]
GPT_4O_MODEL_NAMES_ORDER = [
    # ModelName.GPT_4O_2024_08_06, # 精度が渋いので一旦使わない
    ModelName.GPT_4O_2024_05_13,
]
GPT_4O_MINI_MODEL_NAMES_ORDER = [
    ModelName.GPT_4O_MINI_2024_07_18,
]
O1_PREVIEW_MODEL_NAMES_ORDER = [
    ModelName.O1_PREVIEW_20240912,
]
O1_MINI_MODEL_NAMES_ORDER = [
    ModelName.O1_MINI_20240912,
]
CLAUDE_3_OPUS_MODEL_NAMES_ORDER = [
    ModelName.CLAUDE_3_OPUS_20240229,
]
CLAUDE_3_SONNET_MODEL_NAMES_ORDER = [
    ModelName.CLAUDE_3_SONNET_20240229,
]
CLAUDE_3_HAIKU_MODEL_NAMES_ORDER = [
    ModelName.CLAUDE_3_HAIKU_20240307,
]
CLAUDE_35_SONNET_MODEL_NAMES_ORDER = [
    ModelName.CLAUDE_35_SONNET_V2_20241022,
    ModelName.CLAUDE_35_SONNET_20240620,
]
CLAUDE_35_HAIKU_MODEL_NAMES_ORDER = [
    ModelName.CLAUDE_35_HAIKU_20241022,
]
GEMINI_10_PRO_MODEL_NAMES_ORDER = [
    ModelName.GEMINI_10_PRO,
]
GEMINI_15_PRO_MODEL_NAMES_ORDER = [
    ModelName.GEMINI_15_PRO_002,
    ModelName.GEMINI_15_PRO_001,
    ModelName.GEMINI_15_PRO_PREVIEW_0409,
]
GEMINI_15_FLASH_MODEL_NAMES_ORDER = [
    ModelName.GEMINI_15_FLASH_002,
    ModelName.GEMINI_15_FLASH_001,
]
GEMINI_20_FLASH_MODEL_NAMES_ORDER = [
    ModelName.GEMINI_20_FLASH_EXP,
]


class ModelFamily(str, Enum):
    GPT_35_TURBO = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    O1_PREVIEW = "o1-preview"
    O1_MINI = "o1-mini"
    CLAUDE_3_OPUS = "claude-3-opus"
    CLAUDE_3_SONNET = "claude-3-sonnet"
    CLAUDE_3_HAIKU = "claude-3-haiku"
    CLAUDE_35_SONNET = "claude-3.5-sonnet"
    CLAUDE_35_HAIKU = "claude-3.5-haiku"
    GEMINI_10_PRO = "gemini-1.0-pro"
    GEMINI_15_PRO = "gemini-1.5-pro"
    GEMINI_15_FLASH = "gemini-1.5-flash"
    GEMINI_20_FLASH = "gemini-2.0-flash"

    def get_platforms(self) -> list[Platform]:
        return list({model.to_platform() for model in self._get_model_names_order()})

    def has_jp_region(self) -> bool:
        model_order = self._get_model_names_order()
        return any(not model.is_foreign_region() for model in model_order)

    @property
    def display_name(self) -> str:
        display_names = {
            self.GPT_35_TURBO: "GPT-3.5 Turbo",
            self.GPT_4: "GPT-4",
            self.GPT_4_TURBO: "GPT-4 Turbo",
            self.GPT_4O: "GPT-4o",
            self.GPT_4O_MINI: "GPT-4o mini",
            self.O1_PREVIEW: "o1-preview",
            self.O1_MINI: "o1-mini",
            self.CLAUDE_3_OPUS: "Claude 3 Opus",
            self.CLAUDE_3_SONNET: "Claude 3 Sonnet",
            self.CLAUDE_3_HAIKU: "Claude 3 Haiku",
            self.CLAUDE_35_SONNET: "Claude 3.5 Sonnet",
            self.CLAUDE_35_HAIKU: "Claude 3.5 Haiku",
            self.GEMINI_10_PRO: "Gemini 1.0 Pro",
            self.GEMINI_15_PRO: "Gemini 1.5 Pro",
            self.GEMINI_15_FLASH: "Gemini 1.5 Flash",
            self.GEMINI_20_FLASH: "Gemini 2.0 Flash",
        }
        return display_names[self]

    def is_legacy(self) -> bool:
        return self in {
            ModelFamily.GEMINI_10_PRO,
            ModelFamily.CLAUDE_3_OPUS,
            ModelFamily.CLAUDE_3_SONNET,
            ModelFamily.CLAUDE_3_HAIKU,
        }

    def _get_model_names_order(self) -> list[ModelName]:
        return {
            ModelFamily.GPT_35_TURBO: GPT_35_TURBO_MODEL_NAMES_ORDER,
            ModelFamily.GPT_4: GPT_4_MODEL_NAMES_ORDER,
            ModelFamily.GPT_4_TURBO: GPT_4_TURBO_MODEL_NAMES_ORDER,
            ModelFamily.GPT_4O: GPT_4O_MODEL_NAMES_ORDER,
            ModelFamily.GPT_4O_MINI: GPT_4O_MINI_MODEL_NAMES_ORDER,
            ModelFamily.O1_PREVIEW: O1_PREVIEW_MODEL_NAMES_ORDER,
            ModelFamily.O1_MINI: O1_MINI_MODEL_NAMES_ORDER,
            ModelFamily.CLAUDE_3_OPUS: CLAUDE_3_OPUS_MODEL_NAMES_ORDER,
            ModelFamily.CLAUDE_3_SONNET: CLAUDE_3_SONNET_MODEL_NAMES_ORDER,
            ModelFamily.CLAUDE_35_SONNET: CLAUDE_35_SONNET_MODEL_NAMES_ORDER,
            ModelFamily.CLAUDE_3_HAIKU: CLAUDE_3_HAIKU_MODEL_NAMES_ORDER,
            ModelFamily.CLAUDE_35_HAIKU: CLAUDE_35_HAIKU_MODEL_NAMES_ORDER,
            ModelFamily.GEMINI_10_PRO: GEMINI_10_PRO_MODEL_NAMES_ORDER,
            ModelFamily.GEMINI_15_PRO: GEMINI_15_PRO_MODEL_NAMES_ORDER,
            ModelFamily.GEMINI_15_FLASH: GEMINI_15_FLASH_MODEL_NAMES_ORDER,
            ModelFamily.GEMINI_20_FLASH: GEMINI_20_FLASH_MODEL_NAMES_ORDER,
        }.get(self, [])

    def to_model(
        self,
        allow_foreign_region: AllowForeignRegion,
        additional_platforms: list[Literal[Platform.GCP] | Literal[Platform.OPENAI]],
    ) -> ModelName:
        model_order = self._get_model_names_order()
        # allow_foreign_regionとadditional_platformsに応じて合致したものをフィルタリング
        for model_name in model_order:
            # 海外リージョンを許可しておらず、model_nameが海外リージョンだったらcontinue
            if model_name.is_foreign_region() and not allow_foreign_region:
                continue
            # model_nameがgcpにあるものでかつ追加リージョンにGCPがなければcontinue
            if model_name.is_gcp_only() and Platform.GCP not in additional_platforms:
                continue
            # model_nameがopenaiにあるものでかつ追加リージョンにopenaiがなければcontinue
            if model_name.is_openai_only() and Platform.OPENAI not in additional_platforms:
                continue
            return model_name

        raise ValueError(
            "No model name found that matches the given model series, allow_foreign_region, and additional_platforms."
        )


def get_lightweight_model_orders(
    allow_foreign_region: AllowForeignRegion, platforms: list[Literal[Platform.GCP] | Literal[Platform.OPENAI]]
) -> list[ModelName]:
    # TODO: fix ValueError of query generation by gemini
    # if Platform.GCP in platforms:
    #     return [
    #         ModelName.GEMINI_15_FLASH_001,
    #         ModelName.GPT_35_TURBO_16K,
    #     ]
    if allow_foreign_region.root:
        return [
            ModelName.GPT_4O_MINI_2024_07_18,
            ModelName.GPT_35_TURBO_16K,
        ]
    return [ModelName.GPT_35_TURBO_16K]


def get_response_generator_model_for_text2image(
    allow_foreign_region: AllowForeignRegion,
    platforms: list[Platform],
) -> ModelName:
    # TODO: fix ValueError of query generation by gemini
    if allow_foreign_region.root:
        return ModelName.GPT_4O_MINI_2024_07_18
    return ModelName.GPT_35_TURBO_16K

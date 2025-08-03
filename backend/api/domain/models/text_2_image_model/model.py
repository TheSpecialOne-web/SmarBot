from enum import Enum

from api.domain.models.llm.allow_foreign_region import AllowForeignRegion
from api.domain.models.llm.platform import Platform


class Text2ImageModelName(str, Enum):
    DALL_E_3 = "dall-e-3"

    def is_foreign_region(self) -> bool:
        return self in [
            Text2ImageModelName.DALL_E_3,
        ]


class Text2ImageModelFamily(str, Enum):
    DALL_E_3 = "dall-e-3"

    def has_jp_region(self) -> bool:
        return False

    def get_platforms(self) -> list[Platform]:
        platforms = {
            self.DALL_E_3: [Platform.AZURE],
        }
        return platforms.get(self, [])

    @property
    def display_name(self) -> str:
        display_names = {
            self.DALL_E_3: "DALL·E 3",
        }
        return display_names[self]

    def to_model(
        self,
        allow_foreign_region: AllowForeignRegion,
    ) -> Text2ImageModelName:
        model_order = {
            Text2ImageModelFamily.DALL_E_3: DALL_E_3_MODEL_NAMES_ORDER,
        }.get(self, [])

        for model_name in model_order:
            # 海外リージョンを許可しておらず、model_nameが海外リージョンだったらcontinue
            if model_name.is_foreign_region() and not allow_foreign_region:
                continue
            return model_name

        raise ValueError(f"Invalid model family: {self}")


DALL_E_3_MODEL_NAMES_ORDER = [
    Text2ImageModelName.DALL_E_3,
]

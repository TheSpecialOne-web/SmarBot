from api.domain.models.llm.allow_foreign_region import AllowForeignRegion
from api.domain.models.llm.model import (
    ModelFamily,
    ModelName,
    get_lightweight_model_orders,
)
from api.domain.models.llm.platform import Platform
from api.domain.models.tenant.additional_platform import (
    AdditionalPlatform,
    AdditionalPlatformList,
)


class TestLLMModel:
    def test_to_model_with_allow_foreign_region_and_gcp(self):
        allow_foreign_region = AllowForeignRegion(root=True)
        additional_platforms = AdditionalPlatformList(
            root=[AdditionalPlatform(root=Platform.GCP), AdditionalPlatform(root=Platform.OPENAI)]
        )
        for model in ModelFamily:
            model.to_model(
                allow_foreign_region=allow_foreign_region,
                additional_platforms=[af.root for af in additional_platforms.root],
            )

    def test_to_model_with_allow_foreign_region_without_gcp(self):
        allow_foreign_region = AllowForeignRegion(root=True)
        additional_platforms = AdditionalPlatformList(root=[])
        model_families_without_gcp = [
            model_family for model_family in ModelFamily if Platform.GCP not in model_family.get_platforms()
        ]
        for model_family in model_families_without_gcp:
            model_family.to_model(
                allow_foreign_region=allow_foreign_region,
                additional_platforms=[af.root for af in additional_platforms.root],
            )

    def test_to_model_without_allow_foreign_region_with_gcp(self):
        allow_foreign_region = AllowForeignRegion(root=False)
        additional_platforms = AdditionalPlatformList(
            root=[AdditionalPlatform(root=Platform.GCP), AdditionalPlatform(root=Platform.OPENAI)]
        )
        model_families_with_gcp_and_without_foreign_region = [
            model_family
            for model_family in ModelFamily
            if Platform.GCP in model_family.get_platforms() and model_family.has_jp_region()
        ]
        for model_family in model_families_with_gcp_and_without_foreign_region:
            model_family.to_model(
                allow_foreign_region=allow_foreign_region,
                additional_platforms=[af.root for af in additional_platforms.root],
            )

    def test_to_model_without_allow_foreign_region_without_gcp(self):
        allow_foreign_region = AllowForeignRegion(root=False)
        additional_platforms = AdditionalPlatformList(root=[])
        model_families_without_gcp_and_with_foreign_region = [
            model_family
            for model_family in ModelFamily
            if Platform.GCP not in model_family.get_platforms() and model_family.has_jp_region()
        ]
        for model_family in model_families_without_gcp_and_with_foreign_region:
            model_family.to_model(
                allow_foreign_region=allow_foreign_region,
                additional_platforms=[af.root for af in additional_platforms.root],
            )

    def test_get_platforms(self):
        platforms = {
            ModelFamily.GPT_35_TURBO: [Platform.AZURE],
            ModelFamily.GPT_4: [Platform.AZURE],
            ModelFamily.GPT_4_TURBO: [Platform.AZURE],
            ModelFamily.GPT_4O: [Platform.AZURE],
            ModelFamily.GPT_4O_MINI: [Platform.AZURE],
            ModelFamily.O1_PREVIEW: [Platform.AZURE],
            ModelFamily.O1_MINI: [Platform.AZURE],
            ModelFamily.CLAUDE_3_OPUS: [Platform.GCP],
            ModelFamily.CLAUDE_3_SONNET: [Platform.GCP],
            ModelFamily.CLAUDE_3_HAIKU: [Platform.GCP],
            ModelFamily.CLAUDE_35_SONNET: [Platform.GCP],
            ModelFamily.CLAUDE_35_HAIKU: [Platform.GCP],
            ModelFamily.GEMINI_10_PRO: [Platform.GCP],
            ModelFamily.GEMINI_15_PRO: [Platform.GCP],
            ModelFamily.GEMINI_15_FLASH: [Platform.GCP],
            ModelFamily.GEMINI_20_FLASH: [Platform.GCP],
        }
        for model in ModelFamily:
            assert model.get_platforms() == platforms[model]

    def test_has_jp_region(self):
        jp_region_models = [
            ModelFamily.GPT_35_TURBO,
            ModelFamily.GPT_4,
            ModelFamily.GEMINI_10_PRO,
            ModelFamily.GEMINI_15_PRO,
            ModelFamily.GEMINI_15_FLASH,
        ]
        for model in ModelFamily:
            assert model.has_jp_region() == (model in jp_region_models)

    def test_get_lightweight_model_orders_with_foreign_region(self):
        query_generator_model_orders = get_lightweight_model_orders(
            allow_foreign_region=AllowForeignRegion(root=True), platforms=[Platform.GCP]
        )
        assert query_generator_model_orders == [ModelName.GPT_4O_MINI_2024_07_18, ModelName.GPT_35_TURBO_16K]

    def test_get_lightweight_model_orders_without_foreign_region(self):
        query_generator_model_orders = get_lightweight_model_orders(
            allow_foreign_region=AllowForeignRegion(root=False), platforms=[]
        )
        assert query_generator_model_orders == [ModelName.GPT_35_TURBO_16K]

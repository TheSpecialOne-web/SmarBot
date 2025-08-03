from typing import TYPE_CHECKING
import uuid

from pydantic import BaseModel, Field, computed_field, model_validator

from api.libs.exceptions import BadRequest

from ..group import (
    Id as GroupId,
    Name as GroupName,
)
from ..llm.model import ModelFamily
from ..llm.pdf_parser import PdfParser
from ..search import IndexName
from ..search.endpoint import Endpoint
from ..storage import ContainerName
from ..tenant import Alias, EnableBasicAiWebBrowsing, Tenant
from ..text_2_image_model.model import Text2ImageModelFamily
from .approach import Approach
from .approach_variable import (
    ApproachVariable,
    Name as ApproachVariableName,
    Value as ApproachVariableValue,
)
from .created_at import CreatedAt
from .description import Description
from .document_limit import DocumentLimit
from .enable_follow_up_questions import EnableFollowUpQuestions
from .enable_web_browsing import EnableWebBrowsing
from .endpoint_id import EndpointId, create_endpoint_id
from .example_question import ExampleQuestion
from .icon_color import IconColor
from .icon_url import IconUrl
from .id import Id
from .max_conversation_turns import MaxConversationTurns
from .name import Name
from .query_system_prompt import QuerySystemPrompt
from .response_system_prompt import ResponseSystemPrompt, ResponseSystemPromptHidden
from .search_method import SearchMethod
from .status import Status

if TYPE_CHECKING:
    from ..conversation import UseWebBrowsing


class BotProps(BaseModel):
    name: Name
    description: Description
    index_name: IndexName | None
    container_name: ContainerName | None
    approach: Approach
    pdf_parser: PdfParser
    example_questions: list[ExampleQuestion]
    search_method: SearchMethod | None
    response_generator_model_family: ModelFamily
    image_generator_model_family: Text2ImageModelFamily | None = None
    approach_variables: list[ApproachVariable]
    enable_web_browsing: EnableWebBrowsing
    enable_follow_up_questions: EnableFollowUpQuestions
    icon_url: IconUrl | None = None
    icon_color: IconColor
    max_conversation_turns: MaxConversationTurns | None

    @model_validator(mode="after")
    def check_required_fields(self) -> "BotProps":
        if self.approach in [Approach.CHAT_GPT_DEFAULT, Approach.CUSTOM_GPT]:
            return self
        if self.approach == Approach.TEXT_2_IMAGE:
            if self.image_generator_model_family is None:
                raise BadRequest("画像生成モデルが指定されていません。")
            if self.enable_web_browsing.root is True:
                raise BadRequest("画像生成を使用する際は、Webブラウジングを無効にしてください。")
            return self
        if self.approach == Approach.NEOLLM:
            if self.search_method not in [
                SearchMethod.BM25,
                SearchMethod.SEMANTIC_HYBRID,
                SearchMethod.VECTOR,
                SearchMethod.HYBRID,
            ]:
                raise BadRequest("不正な検索方法です。")
        if self.approach == Approach.URSA:
            if self.index_name is None:
                raise BadRequest("インデックス名が指定されていません。")
            if self.search_method not in [SearchMethod.URSA, SearchMethod.URSA_SEMANTIC]:
                raise BadRequest("不正な検索方法です。")
        return self

    @computed_field  # type: ignore[misc]
    @property
    def response_system_prompt(self) -> ResponseSystemPrompt | None:
        for variable in self.approach_variables:
            if variable.name.value == "response_system_prompt":
                return ResponseSystemPrompt(root=variable.value.value)
        return None

    @computed_field  # type: ignore[misc]
    @property
    def response_system_prompt_hidden(self) -> ResponseSystemPromptHidden | None:
        for variable in self.approach_variables:
            if variable.name.value == "response_system_prompt_hidden":
                return ResponseSystemPromptHidden(root=variable.value.value)
        return None

    @computed_field  # type: ignore[misc]
    @property
    def query_system_prompt(self) -> QuerySystemPrompt | None:
        for variable in self.approach_variables:
            if variable.name.value == "query_system_prompt":
                return QuerySystemPrompt(root=variable.value.value)
        return None

    @computed_field  # type: ignore[misc]
    @property
    def document_limit(self) -> DocumentLimit:
        for variable in self.approach_variables:
            if variable.name.value == "document_limit":
                return DocumentLimit(root=int(variable.value.value))
        return DocumentLimit()

    @computed_field  # type: ignore[misc]
    @property
    def search_service_endpoint(self) -> Endpoint | None:
        for variable in self.approach_variables:
            if variable.name.value == "search_service_endpoint":
                return Endpoint(root=variable.value.value)
        return None


class BotForCreate(BotProps):
    endpoint_id: EndpointId = Field(default_factory=create_endpoint_id)
    status: Status = Status.ACTIVE

    @model_validator(mode="after")
    def check_legacy_model_family(self) -> "BotForCreate":
        if self.response_generator_model_family.is_legacy():
            raise BadRequest("使用できないモデルです。")
        return self

    @classmethod
    def create_custom_gpt(
        cls,
        tenant_alias: Alias,
        name: Name,
        description: Description,
        example_questions: list[ExampleQuestion],
        response_generator_model_family: ModelFamily,
        response_system_prompt: ResponseSystemPrompt,
        document_limit: DocumentLimit,
        pdf_parser: PdfParser,
        enable_web_browsing: EnableWebBrowsing,
        icon_color: IconColor,
        max_conversation_turns: MaxConversationTurns | None,
    ) -> "BotForCreate":
        # ユーザー側からは ai_vision は選べない
        if pdf_parser not in [PdfParser.PYPDF, PdfParser.DOCUMENT_INTELLIGENCE, PdfParser.LLM_DOCUMENT_READER]:
            raise BadRequest("不正なドキュメント読み取りオプションです。")

        if document_limit.root > 20 or document_limit.root < 1:
            raise BadRequest("1 以上 20 以下の数値を入力してください。")

        return cls(
            name=name,
            description=description,
            index_name=None,
            container_name=ContainerName(root=f"{tenant_alias.root}-custom-gpt-{uuid.uuid4()}"),
            approach=Approach.CUSTOM_GPT,
            pdf_parser=pdf_parser,
            example_questions=example_questions,
            search_method=None,
            response_generator_model_family=response_generator_model_family,
            image_generator_model_family=None,
            approach_variables=[
                ApproachVariable(
                    name=ApproachVariableName(value="response_system_prompt"),
                    value=ApproachVariableValue(value=response_system_prompt.root),
                ),
                ApproachVariable(
                    name=ApproachVariableName(value="document_limit"),
                    value=ApproachVariableValue(value=str(document_limit.root)),
                ),
            ],
            enable_web_browsing=enable_web_browsing,
            enable_follow_up_questions=EnableFollowUpQuestions(root=False),
            icon_url=None,
            icon_color=icon_color,
            max_conversation_turns=max_conversation_turns,
        )

    @classmethod
    def create_neollm(
        cls,
        tenant_alias: Alias,
        name: Name,
        description: Description,
        example_questions: list[ExampleQuestion],
        search_method: SearchMethod,
        response_generator_model_family: ModelFamily,
        response_system_prompt: ResponseSystemPrompt,
        document_limit: DocumentLimit,
        pdf_parser: PdfParser,
        enable_web_browsing: EnableWebBrowsing,
        enable_follow_up_questions: EnableFollowUpQuestions,
        icon_color: IconColor,
        max_conversation_turns: MaxConversationTurns | None,
    ) -> "BotForCreate":
        # ユーザー側からは ai_vision は選べない
        if pdf_parser not in [PdfParser.PYPDF, PdfParser.DOCUMENT_INTELLIGENCE, PdfParser.LLM_DOCUMENT_READER]:
            raise BadRequest("不正なドキュメント読み取りオプションです")

        if document_limit.root > 20 or document_limit.root < 1:
            raise BadRequest("1 以上 20 以下の数値を入力してください。")

        # ユーザー側からは BM25 と SEMANTIC_HYBRID 以外は選べない
        if search_method not in [
            SearchMethod.BM25,
            SearchMethod.SEMANTIC_HYBRID,
        ]:
            raise BadRequest("不正な検索方法です。")
        return cls(
            name=name,
            description=description,
            index_name=None,
            container_name=ContainerName(root=f"{tenant_alias.root}-neollm-{uuid.uuid4()}"),
            approach=Approach.NEOLLM,
            pdf_parser=pdf_parser,
            example_questions=example_questions,
            search_method=search_method,
            response_generator_model_family=response_generator_model_family,
            image_generator_model_family=None,
            approach_variables=[
                ApproachVariable(
                    name=ApproachVariableName(value="response_system_prompt"),
                    value=ApproachVariableValue(value=response_system_prompt.root),
                ),
                ApproachVariable(
                    name=ApproachVariableName(value="document_limit"),
                    value=ApproachVariableValue(value=str(document_limit.root)),
                ),
            ],
            enable_web_browsing=enable_web_browsing,
            enable_follow_up_questions=enable_follow_up_questions,
            icon_url=None,
            icon_color=icon_color,
            max_conversation_turns=max_conversation_turns,
        )

    def set_search_service_endpoint(self, endpoint: Endpoint) -> None:
        self.approach_variables.append(
            ApproachVariable(
                name=ApproachVariableName(value="search_service_endpoint"),
                value=ApproachVariableValue(value=endpoint.root),
            )
        )


class BotForUpdate(BotProps):
    @model_validator(mode="after")
    def check_legacy_model_family(self) -> "BotForUpdate":
        if self.response_generator_model_family.is_legacy():
            raise BadRequest("使用できないモデルです。")
        return self

    @classmethod
    def by_user(
        cls,
        current: "Bot",
        name: Name,
        description: Description,
        example_questions: list[ExampleQuestion],
        search_method: SearchMethod | None,
        approach: Approach,
        response_generator_model_family: ModelFamily,
        response_system_prompt: ResponseSystemPrompt,
        document_limit: DocumentLimit,
        pdf_parser: PdfParser,
        enable_web_browsing: EnableWebBrowsing,
        enable_follow_up_questions: EnableFollowUpQuestions,
        icon_color: IconColor,
        max_conversation_turns: MaxConversationTurns | None,
    ) -> "BotForUpdate":
        # CUSTOM_GPT と NEOLLM 以外は更新不可
        EDITABLE_APPROACHES = [Approach.CUSTOM_GPT, Approach.NEOLLM]
        if current.approach not in EDITABLE_APPROACHES or approach not in EDITABLE_APPROACHES:
            raise BadRequest("アプローチを変更することができません")

        # pdf_parser が ai_vision の場合は更新不可
        if current.pdf_parser == PdfParser.AI_VISION and pdf_parser != PdfParser.AI_VISION:
            raise BadRequest("ドキュメント読み取りオプションを変更することができません")

        if document_limit.root > 20 or document_limit.root < 1:
            raise BadRequest("1 以上 20 以下の数値を入力してください。")

        approach_variables = [
            variable for variable in current.approach_variables if variable.name.value != "response_system_prompt"
        ]
        if not response_system_prompt.is_empty():
            approach_variables.append(
                ApproachVariable(
                    name=ApproachVariableName(value="response_system_prompt"),
                    value=ApproachVariableValue(value=response_system_prompt.root),
                )
            )
        approach_variables.append(
            ApproachVariable(
                name=ApproachVariableName(value="document_limit"),
                value=ApproachVariableValue(value=str(document_limit.root)),
            )
        )

        return cls(
            name=name,
            description=description,
            example_questions=example_questions,
            index_name=current.index_name,
            container_name=current.container_name,
            approach=approach,
            pdf_parser=pdf_parser,
            search_method=search_method,
            image_generator_model_family=current.image_generator_model_family,
            response_generator_model_family=response_generator_model_family,
            approach_variables=approach_variables,
            enable_web_browsing=enable_web_browsing,
            enable_follow_up_questions=enable_follow_up_questions,
            icon_url=current.icon_url,
            icon_color=icon_color,
            max_conversation_turns=max_conversation_turns,
        )


class Bot(BotProps):
    id: Id
    group_id: GroupId
    created_at: CreatedAt
    status: Status
    endpoint_id: EndpointId

    def is_basic_ai(self) -> bool:
        return self.approach in [Approach.CHAT_GPT_DEFAULT, Approach.TEXT_2_IMAGE]

    def id_filter_for_search_index(self) -> str:
        return f"bot_id eq {self.id.value}"

    def update(self, update_param: BotForUpdate):
        if self.approach in [Approach.CHAT_GPT_DEFAULT, Approach.URSA] and update_param.approach != self.approach:
            raise BadRequest("アプローチを変更することができません")
        if self.approach == Approach.URSA and update_param.search_method != self.search_method:
            raise BadRequest("検索方法は指定できません。")
        self.name = update_param.name
        self.description = update_param.description
        self.index_name = update_param.index_name if update_param.index_name else self.index_name
        self.container_name = update_param.container_name if update_param.container_name else self.container_name
        self.approach = update_param.approach
        self.pdf_parser = update_param.pdf_parser
        self.example_questions = update_param.example_questions
        self.search_method = update_param.search_method
        self.response_generator_model_family = update_param.response_generator_model_family
        self.image_generator_model_family = (
            update_param.image_generator_model_family
            if update_param.image_generator_model_family
            else self.image_generator_model_family
        )
        self.approach_variables = update_param.approach_variables
        self.enable_web_browsing = update_param.enable_web_browsing
        self.enable_follow_up_questions = update_param.enable_follow_up_questions
        self.icon_color = update_param.icon_color
        self.max_conversation_turns = update_param.max_conversation_turns

    def update_icon_url(self, icon_url: IconUrl | None):
        self.icon_url = icon_url

    def validate_allowed_model_families(self, allowed_model_families: list[ModelFamily | Text2ImageModelFamily]):
        # 画像生成の際は response_generator_model_family のバリデーションを無視する
        if (
            self.approach != Approach.TEXT_2_IMAGE
            and self.response_generator_model_family not in allowed_model_families
        ):
            raise BadRequest("使用できないモデルです。")
        if (
            self.image_generator_model_family is not None
            and self.image_generator_model_family not in allowed_model_families
        ):
            raise BadRequest("使用できないモデルです。")

    def archive(self):
        if self.status == Status.ARCHIVED:
            raise BadRequest("すでにアーカイブされています。")
        if self.status == Status.DELETING:
            raise BadRequest("削除中のアシスタントです。")
        self.status = Status.ARCHIVED

    def restore(self):
        if self.status == Status.ACTIVE:
            raise BadRequest("アクティブなアシスタントです。")
        if self.status == Status.DELETING:
            raise BadRequest("削除中のアシスタントです。")
        self.status = Status.ACTIVE

    def delete(self):
        # TODO: 運営画面から削除するときと、ユーザーが削除するときで処理を分ける
        self.status = Status.DELETING

    def delete_basic_ai(self):
        if not self.is_basic_ai():
            raise BadRequest("基盤モデルではありません。")
        self.status = Status.BASIC_AI_DELETED

    def enable_web_browsing_with_tenant_setting(self, enable_basic_ai_web_browsing: EnableBasicAiWebBrowsing) -> bool:
        if self.approach in [Approach.CUSTOM_GPT, Approach.NEOLLM]:
            return self.enable_web_browsing.root
        if self.is_basic_ai():
            return enable_basic_ai_web_browsing.root
        return False

    def use_query_generator(
        self, use_web_browsing: "UseWebBrowsing", enable_basic_ai_web_browsing: EnableBasicAiWebBrowsing
    ) -> bool:
        return self.approach in [
            Approach.NEOLLM,
            Approach.URSA,
            Approach.TEXT_2_IMAGE,
        ] or (self.enable_web_browsing_with_tenant_setting(enable_basic_ai_web_browsing) and use_web_browsing.root)


class BotWithGroupName(Bot):
    group_name: GroupName


class BotWithTenant(Bot):
    tenant: Tenant


class BasicAiForCreate(BotForCreate):
    def __init__(self, tenant: Tenant, model_family: ModelFamily):
        super().__init__(
            name=Name(value=model_family.display_name),
            description=Description(
                value="何かお困りのことはありませんか？\n※社内情報に関する質問にはお答えできません。",
            ),
            index_name=None,
            container_name=ContainerName(root=f"{tenant.alias.root}-{uuid.uuid4()}"),
            approach=Approach.CHAT_GPT_DEFAULT,
            pdf_parser=PdfParser(tenant.basic_ai_pdf_parser.value),
            example_questions=[
                ExampleQuestion(value="プロジェクト管理のベストプラクティスについて教えてください。"),
                ExampleQuestion(value="リモートワークの効果的な実施方法について教えてください。"),
                ExampleQuestion(value="プレゼン資料の作成を手伝ってください。"),
            ],
            search_method=None,
            response_generator_model_family=model_family,
            enable_web_browsing=EnableWebBrowsing(root=tenant.enable_basic_ai_web_browsing.root),
            enable_follow_up_questions=EnableFollowUpQuestions(root=True),
            icon_url=None,
            icon_color=IconColor(root="#AA68FF"),
            max_conversation_turns=MaxConversationTurns(root=5),
            approach_variables=[],
        )


class Text2ImageBotForCreate(BotForCreate):
    def __init__(self, tenant: Tenant, model_family: Text2ImageModelFamily):
        super().__init__(
            name=Name(value=model_family.display_name),
            description=Description(
                value="入力された指示に従い、画像を生成します。",
            ),
            index_name=None,
            container_name=ContainerName(root=f"{tenant.alias.root}-{uuid.uuid4()}"),
            approach=Approach.TEXT_2_IMAGE,
            pdf_parser=PdfParser(tenant.basic_ai_pdf_parser.value),
            example_questions=[
                ExampleQuestion(value="プロジェクト管理のベストプラクティスについて教えてください。"),
                ExampleQuestion(value="リモートワークの効果的な実施方法について教えてください。"),
                ExampleQuestion(value="プレゼン資料の作成を手伝ってください。"),
            ],
            search_method=None,
            response_generator_model_family=ModelFamily.GPT_35_TURBO,
            image_generator_model_family=model_family,
            enable_web_browsing=EnableWebBrowsing(root=False),
            enable_follow_up_questions=EnableFollowUpQuestions(root=False),
            icon_url=None,
            icon_color=IconColor(root="#FFB74D"),
            max_conversation_turns=MaxConversationTurns(root=5),
            approach_variables=[],
        )

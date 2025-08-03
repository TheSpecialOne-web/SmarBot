import ast
from copy import deepcopy
import random
import re
from typing import Any, Final, Generator

from azure.identity import DefaultAzureCredential
from neollm.exceptions import ContentFilterError
from neollm.types import LLMSettings
from tenacity import retry, stop_after_attempt, wait_exponential
import tiktoken

from api.domain.models.conversation import FollowUpQuestion, ImageUrl, Title
from api.domain.models.conversation.conversation_turn import Turn
from api.domain.models.data_point import DataPoint
from api.domain.models.llm import ModelName, Platform
from api.domain.models.query import Queries
from api.domain.models.term import NameV2, TermsDict, TermV2
from api.domain.models.text_2_image_model.model import Text2ImageModelName
from api.domain.services.llm import (
    ILLMService,
    QueryGeneratorInput,
    QueryGeneratorOutput,
    ResponseGeneratorInput,
    ResponseGeneratorStreamOutput,
    UrsaQuestionGeneratorInput,
    UrsaResponseGeneratorInput,
)
from api.domain.services.llm.llm import Dalle3ResponseGeneratorInput
from api.infrastructures.llm.libs.image_generator.image_generator import ImageGenerator
from api.libs.logging import get_logger
from api.libs.retry import retry_remote_protocol_error

from .azure_openai.client import AOAIClient
from .gcp.client import VertexAIClient
from .libs.conversation_title_generator.conversation_title_generator import (
    ConversationTitleGenerator,
)
from .libs.query_generator.foundation_model_qg_dalle3 import QueryGeneratorForDalle3
from .libs.query_generator.query_generator import QueryGenerator
from .libs.query_generator.ursa_query_generator import UrsaQueryGenerator
from .libs.question_generator.question_generator import QuestionGenerator
from .libs.question_generator.ursa_question_generator import UrsaQuestionGenerator
from .libs.response_generator.assistant_rg import AssistantResponseGenerator
from .libs.response_generator.foudation_model_rg import FoundationResponseGenerator
from .libs.response_generator.foundation_model_rg_dalle3 import (
    ResponseGeneratorForDalle3,
)

EMBEDDINGS_MODEL: Final[str] = "text-embedding-ada-002"
EMBEDDINGS_TOKEN_LIMIT = 8192
QUESTION_GENERATOR_MODEL: Final[str] = "gpt-3.5-turbo-16k"

NO_USER_INPUT_TITLE = "添付ファイルの読み込み"


class LLMService(ILLMService):
    def __init__(self, azure_credential: DefaultAzureCredential) -> None:
        self.logger = get_logger()
        self.aoai_client = AOAIClient(azure_credential=azure_credential)
        self.vertex_ai_client = VertexAIClient()

    @retry(reraise=True, wait=wait_exponential(), stop=stop_after_attempt(3))
    def generate_embeddings(self, text: str, use_foreign_region: bool = False) -> list[float]:
        cilent = self.aoai_client.get_azure_openai_client(
            region="japaneast" if not use_foreign_region else "eastus2",
        )
        encoding_model = tiktoken.encoding_for_model(EMBEDDINGS_MODEL)
        text_ = text
        if len(encoding_model.encode(text_)) > EMBEDDINGS_TOKEN_LIMIT:
            text_ = text_[:5000]
        response = cilent.embeddings.create(input=text_, model=EMBEDDINGS_MODEL)
        embeddings = response.data[0].embedding
        return embeddings

    def generate_conversation_title(self, model_name: ModelName, turn_list: list[Turn]) -> Title:
        if len(turn_list) == 0:
            return Title()
        if len(turn_list[0].user.root) == 0:
            return Title(root=NO_USER_INPUT_TITLE)
        conversation_title_generator = ConversationTitleGenerator(
            **self._get_myllm_settings(model_name, {"seed": 42, "temperature": 0, "max_tokens": 50}),
        )
        try:
            it = conversation_title_generator.call_stream(turn_list)
            title = ""
            for chunk in it:
                if isinstance(chunk, str):
                    title += chunk
            return Title(root=title)
        except ContentFilterError as e:
            self.logger.warning("ContentFilterError", exc_info=e)
            return Title()
        except Exception as e:
            self.logger.error("Failed to generate conversation title", exc_info=e)
            return Title()

    def generate_query(self, inputs: QueryGeneratorInput) -> QueryGeneratorOutput:
        query_generator = QueryGenerator(
            **self._get_myllm_settings(inputs.model),
        )
        return query_generator(inputs)

    def generate_query_for_dalle3(self, inputs: QueryGeneratorInput) -> QueryGeneratorOutput:
        query_generator = QueryGeneratorForDalle3(
            **self._get_myllm_settings(inputs.model),
        )
        return query_generator(inputs)

    def generate_ursa_query(self, inputs: QueryGeneratorInput) -> QueryGeneratorOutput:
        query_generator = UrsaQueryGenerator(
            **self._get_myllm_settings(inputs.model),
        )
        return query_generator(inputs)

    def generate_image(self, model: Text2ImageModelName, prompt: str) -> ImageUrl:
        image_generator = ImageGenerator(
            client=self.aoai_client.get_azure_openai_client_for_dalle3(),
            model=model,
        )
        return image_generator.generate_image(prompt)

    @retry_remote_protocol_error
    def generate_response_with_internal_data(
        self, inputs: ResponseGeneratorInput
    ) -> Generator[ResponseGeneratorStreamOutput, None, None]:
        response_generator = AssistantResponseGenerator(
            **self._get_myllm_settings(inputs.model),
        )
        return response_generator.generate_response_stream(inputs)

    @retry_remote_protocol_error
    def generate_response_without_internal_data(
        self, inputs: ResponseGeneratorInput
    ) -> Generator[ResponseGeneratorStreamOutput, None, None]:
        response_generator = FoundationResponseGenerator(
            **self._get_myllm_settings(inputs.model),
        )
        return response_generator.generate_response_stream(inputs)

    def generate_response_for_dalle3(
        self, inputs: Dalle3ResponseGeneratorInput
    ) -> Generator[ResponseGeneratorStreamOutput, None, None]:
        response_generator = ResponseGeneratorForDalle3(
            **self._get_myllm_settings(inputs.model),
        )
        return response_generator.generate_response_stream(inputs)

    def _get_myllm_settings(self, model_name: ModelName, llm_settings: LLMSettings | None = None) -> dict[str, Any]:
        llm_settings_ = deepcopy(llm_settings) if llm_settings is not None else {"temperature": 0.2}

        platform = model_name.to_platform()
        if platform == Platform.AZURE:
            client_settings = self.aoai_client.get_client_settings(model_name)

        elif platform == Platform.OPENAI:
            client_settings = {}

        elif platform == Platform.GCP:
            if "seed" in llm_settings_:
                del llm_settings_["seed"]
            if model_name.is_claude():
                client_settings = self.vertex_ai_client.get_client_settings_for_claude(model_name=model_name)
            elif model_name.is_gemini():
                client_settings = self.vertex_ai_client.get_client_settings_for_gemini(model_name=model_name)

        else:
            raise Exception(f"Unsupported platform: {platform}")

        return {
            "model": model_name.to_model(),
            "platform": platform.value,
            "llm_settings": llm_settings_,
            "client_settings": client_settings,
        }

    def generate_ursa_response(
        self, inputs: UrsaResponseGeneratorInput
    ) -> Generator[ResponseGeneratorStreamOutput, None, None]:
        query_for_display = (
            "」、「".join(inputs.additional_kwargs.get("query_for_display") or [])
            if len(inputs.queries) > 0
            else "検索語句がありません。"
        )
        query_for_display = f"「{query_for_display}」\n"

        filter = inputs.additional_kwargs.get("filter")
        understandable_filter = (
            self._make_filters_understandable("".join(filter))
            if filter is not None
            else "「フィルタはありません。」\n"
        )
        if understandable_filter == "":
            understandable_filter = "「フィルタはありません。」\n"
        query_section = f"検索語句:{query_for_display}\n\n"
        filter_section = f"フィルタ:{understandable_filter}\n\n"
        yield f"{query_section}{filter_section}"

    def _make_filters_understandable(self, filter_string: str) -> str:
        """
        フィルタ文字列を人間が読みやすい形に変換する
        """
        filter_string_list = filter_string.split("and")
        replacements = {
            "branch": "支店:",
            "extention": "拡張子:",
            "author": "",
            "year": "年度:",
            "eq": "",
            "search.ismatch": "作成者:",
            "simple": "",
            "all": "",
            "or": "または",
            "'": "",
            ",": "",
            "(": "",
            ")": "",
            "document_type": "データの種類",
            "データの種類 ne 安全関連": "",
            " ": "",
            "データの種類eq安全関連": "データの種類 eq 安全関連",
        }
        formatted_string_list = []
        for filter_word in filter_string_list:
            for key, value in replacements.items():
                filter_word = filter_word.replace(key, value)
            formatted_string_list.append(f"「{filter_word}」") if filter_word != "" else None
        filter_string = "、".join(formatted_string_list)
        filter_string = re.sub(r"''\s*", "", filter_string)
        filter_string = re.sub(r"\\", "", filter_string)
        return filter_string

    def generate_questions(self, model_name: ModelName, data_points: list[DataPoint]) -> list[FollowUpQuestion]:
        DISPLAY_LIMIT = 2
        self.question_generator = QuestionGenerator(
            **self._get_myllm_settings(model_name, {"seed": 42, "temperature": 0, "max_tokens": 100}),
        )

        selected_data_points = random.sample(data_points, min(len(data_points), DISPLAY_LIMIT))

        def generate_question(data_points: list[DataPoint]) -> str:
            it = self.question_generator.call_stream(data_points)
            follow_up_question = ""
            while True:
                try:
                    item = next(it)
                    if isinstance(item, str):
                        follow_up_question += item
                except ContentFilterError:
                    break
                except StopIteration:
                    break
            return follow_up_question

        questions = generate_question(selected_data_points)
        try:
            follow_up_questions: list[str] = ast.literal_eval(f"[{questions}]")
            return [FollowUpQuestion(root=follow_up_question) for follow_up_question in follow_up_questions][
                :DISPLAY_LIMIT
            ]
        except (SyntaxError, ValueError):
            return []
        except Exception as e:
            # 失敗した場合でもエラーを出さないようにする
            self.logger.error("Failed to generate follow-up questions", exc_info=e)
            return []

    def generate_ursa_questions(self, inputs: UrsaQuestionGeneratorInput) -> list[FollowUpQuestion]:
        qg = UrsaQuestionGenerator(
            **self._get_myllm_settings(
                ModelName(QUESTION_GENERATOR_MODEL), {"seed": 42, "temperature": 0, "max_tokens": 300}
            ),
        )

        return qg(inputs)

    def update_query_with_terms(self, queries: Queries, terms: list[TermV2]) -> tuple[Queries, TermsDict]:
        """
        用語集がある場合の検索クエリアップデート

        Args:
            queries (Queries): 検索クエリ
            terms (list[TermV2]): 用語集

        Returns:
            tuple[Queries, TermsDict]: 同義語などを考慮した検索クエリ、クエリとその説明がペアになった辞書
        """

        desc2names: dict[str, list[str]] = {
            term.description.root: [name.root for name in term.names] for term in terms
        }
        key2desc: dict[str, str] = {name.to_key(): term.description.root for term in terms for name in term.names}

        terms_dict: dict[str, str] = {}

        search_queries: list[str] = []
        for q in queries.to_string_list():
            # 順番を保持するため、最初にクエリを追加
            search_queries.append(q)
            preprocessed_q = NameV2(root=q).to_key()
            if preprocessed_q not in key2desc:
                continue
            same_desc_names = desc2names[key2desc[preprocessed_q]]
            search_queries.extend([name for name in same_desc_names if name != q])
            terms_dict[q] = key2desc[preprocessed_q]

        return Queries.from_list(search_queries), TermsDict(root=terms_dict)

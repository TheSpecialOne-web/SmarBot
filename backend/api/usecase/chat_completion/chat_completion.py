from abc import ABC, abstractmethod
from datetime import datetime

from injector import inject

from api.domain.models import (
    api_key as api_key_domain,
    bot as bot_domain,
    chat_completion as chat_completion_domain,
    chat_completion_export as chat_completion_export_domain,
    tenant as tenant_domain,
    term as term_domain,
    token as token_domain,
    user as user_domain,
)
from api.domain.models.bot import (
    Approach,
    ResponseSystemPrompt,
    ResponseSystemPromptHidden,
    SearchMethod,
)
from api.domain.models.chat_completion.data_point import ChatCompletionDataPoint
from api.domain.models.data_point import (
    CiteNumber,
    DataPoint,
    DataPointWithoutCiteNumber,
    Type,
)
from api.domain.models.llm import ModelName, get_lightweight_model_orders
from api.domain.models.query import Queries
from api.domain.models.term import TermsDict
from api.domain.services.blob_storage import IBlobStorageService
from api.domain.services.cognitive_search import ICognitiveSearchService
from api.domain.services.llm import (
    ILLMService,
    QueryGeneratorInput,
    ResponseGeneratorInput,
)
from api.domain.services.llm.llm import QueryGeneratorOutput
from api.domain.services.queue_storage.queue_storage import IQueueStorageService
from api.libs.exceptions import BadRequest, HTTPException, NotFound
from api.libs.logging import get_logger

from .types import (
    BotWithApiKeys,
    ChatCompletionAnswer,
    ChatCompletionDataPoints,
    ChatCompletionId,
    ChatCompletionWithBotAndApiKey,
    CreateChatCompletionInput,
    CreateChatCompletionNonStreamOutput,
    CreateChatCompletionStreamOutput,
    UpdateChatCompletionFeedbackCommentInput,
    UpdateChatCompletionFeedbackEvaluationInput,
)


class IChatCompletionUseCase(ABC):
    @abstractmethod
    def create_chat_completion(self, input: CreateChatCompletionInput) -> CreateChatCompletionNonStreamOutput:
        pass

    @abstractmethod
    def create_chat_completion_stream(self, input: CreateChatCompletionInput) -> CreateChatCompletionStreamOutput:
        pass

    @abstractmethod
    def get_chat_completions_for_download(
        self,
        bot_id: bot_domain.Id | None,
        api_key_id: api_key_domain.Id | None,
        start_date_time: datetime,
        end_date_time: datetime,
        tenant_id: tenant_domain.Id,
    ) -> list[ChatCompletionWithBotAndApiKey]:
        pass

    @abstractmethod
    def create_chat_completion_export(
        self,
        tenant_id: tenant_domain.Id,
        chat_completion_export_for_create: chat_completion_export_domain.ChatCompletionExportForCreate,
    ) -> chat_completion_export_domain.ChatCompletionExportWithUser:
        pass

    @abstractmethod
    def get_chat_completion_exports_with_user(
        self,
        tenant_id: tenant_domain.Id,
    ) -> list[chat_completion_export_domain.ChatCompletionExportWithUser]:
        pass

    @abstractmethod
    def delete_chat_completion_exports(
        self, tenant_id: tenant_domain.Id, chat_completion_export_ids: list[chat_completion_export_domain.Id]
    ) -> None:
        pass

    @abstractmethod
    def get_chat_completion_export_signed_url(
        self, tenant: tenant_domain.Tenant, chat_completion_export_id: chat_completion_export_domain.Id
    ) -> chat_completion_export_domain.SignedUrl:
        pass

    @abstractmethod
    def update_chat_completion_feedback_evaluation(self, input: UpdateChatCompletionFeedbackEvaluationInput) -> None:
        pass

    @abstractmethod
    def update_chat_completion_feedback_comment(self, input: UpdateChatCompletionFeedbackCommentInput) -> None:
        pass


class ChatCompletionUseCase(IChatCompletionUseCase):
    @inject
    def __init__(
        self,
        term_repo: term_domain.ITermV2Repository,
        llm_service: ILLMService,
        cognitive_search_service: ICognitiveSearchService,
        chat_completion_repo: chat_completion_domain.IChatCompletionRepository,
        bot_repo: bot_domain.IBotRepository,
        api_key_repo: api_key_domain.IApiKeyRepository,
        user_repo: user_domain.IUserRepository,
        chat_completion_export_repo: chat_completion_export_domain.IChatCompletionExportRepository,
        queue_storage_service: IQueueStorageService,
        blob_storage_service: IBlobStorageService,
        tenant_repo: tenant_domain.ITenantRepository,
    ) -> None:
        self.logger = get_logger()
        self.term_repo = term_repo
        self.llm_service = llm_service
        self.cognitive_search_service = cognitive_search_service
        self.chat_completion_repo = chat_completion_repo
        self.chat_completion_export_repo = chat_completion_export_repo
        self.bot_repo = bot_repo
        self.api_key_repo = api_key_repo
        self.user_repo = user_repo
        self.chat_completion_export_repo = chat_completion_export_repo
        self.queue_storage_service = queue_storage_service
        self.blob_storage_service = blob_storage_service
        self.tenant_repo = tenant_repo

    def create_chat_completion(self, input: CreateChatCompletionInput) -> CreateChatCompletionNonStreamOutput:
        out = self.create_chat_completion_stream(input)
        answer = chat_completion_domain.Content(root="")
        data_points = []
        chat_completion_id = None
        for item in out:
            if isinstance(item, ChatCompletionAnswer):
                answer = item.answer
            if isinstance(item, ChatCompletionDataPoints):
                data_points = item.data_points
            if isinstance(item, ChatCompletionId):
                chat_completion_id = item.id

        if chat_completion_id is None:
            raise Exception("chat_completion_id must not be None when returning the output.")

        return CreateChatCompletionNonStreamOutput(id=chat_completion_id, answer=answer, data_points=data_points)

    def _calculate_token_count(
        self,
        response_system_prompt: ResponseSystemPrompt | None,
        response_system_prompt_hidden: ResponseSystemPromptHidden | None,
        use_query_generator: bool,
        terms_dict: TermsDict,
        used_data_points: list[DataPoint],
        history: chat_completion_domain.Messages,
        answer: str,
        model_name: ModelName,
    ) -> token_domain.TokenCount:
        QUERY_GENERATOR_TOKEN = 500
        RESPONSE_GENERATOR_TOKEN = 200
        tokens = token_domain.Token(root=0)

        if response_system_prompt is not None:
            tokens += token_domain.Token.from_string(response_system_prompt.root)
        if response_system_prompt_hidden is not None:
            tokens += token_domain.Token.from_string(response_system_prompt_hidden.root)

        for message in history.root:
            tokens += token_domain.Token.from_string(message.content.root)

        tokens += token_domain.Token.from_string(answer)

        if use_query_generator:
            tokens += token_domain.Token(root=QUERY_GENERATOR_TOKEN)
        tokens += token_domain.Token(root=RESPONSE_GENERATOR_TOKEN)

        for data_point in used_data_points:
            tokens += token_domain.Token.from_string(data_point.content.root)

        for key, value in terms_dict.root.items():
            tokens += token_domain.Token.from_string(key)
            tokens += token_domain.Token.from_string(value)

        total_tokens = token_domain.TokenCount.from_token(tokens, model_name, True)

        return total_tokens

    def create_chat_completion_stream(self, input: CreateChatCompletionInput) -> CreateChatCompletionStreamOutput:
        tenant = input.tenant
        bot = input.bot
        api_key = input.api_key
        chat_completion_for_create = input.chat_completion

        # 使用できるモデルかどうかを確認する
        bot.validate_allowed_model_families(tenant.allowed_model_families)

        if bot.approach not in [Approach.NEOLLM, Approach.CUSTOM_GPT]:
            raise BadRequest("Invalid approach")

        chat_completion = self.chat_completion_repo.create(
            api_key_id=api_key.id, chat_completion=chat_completion_domain.ChatCompletion.create_empty()
        )
        yield ChatCompletionId(id=chat_completion.id)

        response_generator_model = bot.response_generator_model_family.to_model(
            allow_foreign_region=tenant.allow_foreign_region,
            additional_platforms=[platform.root for platform in tenant.additional_platforms.root],
        )

        terms = self.term_repo.find_by_bot_id(bot_id=bot.id)

        messages = chat_completion_for_create.messages

        use_query_generator = bot.approach == Approach.NEOLLM
        query_generator_output = None
        if use_query_generator:
            for model in get_lightweight_model_orders(
                tenant.allow_foreign_region, [p.root for p in tenant.additional_platforms.root]
            ):
                try:
                    query_generator_output = self.llm_service.generate_query(
                        QueryGeneratorInput(
                            model=model,
                            messages=messages.root,
                            tenant_name=tenant.name,
                            query_system_prompt=bot.query_system_prompt,
                        )
                    )
                    break
                except Exception as e:
                    msg = f"Failed to generate query with model {model.value}"
                    if isinstance(e, HTTPException) and e.status_code >= 400 and e.status_code < 500:
                        self.logger.warning(msg, exc_info=e)
                    else:
                        self.logger.error(msg, exc_info=e)
                    continue
            if query_generator_output is None:
                query_generator_output = QueryGeneratorOutput(
                    queries=Queries.from_list([messages.root[-1].content.root]),
                    input_token=0,
                    output_token=0,
                )

        # 用語集がある場合の検索クエリアップデート
        search_queries, terms_dict = self.llm_service.update_query_with_terms(
            queries=query_generator_output.queries if query_generator_output is not None else Queries.from_list([]),
            terms=terms,
        )

        data_points_without_cite_number: list[DataPointWithoutCiteNumber] = []
        use_internal_data = bot.approach == Approach.NEOLLM

        # if ドキュメント
        if use_internal_data:
            embeddings = []
            if bot.search_method is not None and bot.search_method.should_create_embeddings():
                embeddings = self.llm_service.generate_embeddings(
                    text=search_queries.to_string(delimiter=" "),
                )
            endpoint = input.tenant.search_service_endpoint
            index_name = input.tenant.index_name
            internal_data_points = self.cognitive_search_service.search_documents(
                endpoint=endpoint,
                index_name=index_name,
                queries=search_queries,
                document_limit=bot.document_limit,
                filter=bot.id_filter_for_search_index(),
                search_method=bot.search_method or SearchMethod.BM25,
                embeddings=embeddings,
                additional_kwargs={},
            )
            data_points_without_cite_number.extend(internal_data_points)

        data_points = [
            ChatCompletionDataPoint(
                cite_number=CiteNumber(root=idx + 1),
                **data_point.model_dump(),
            )
            for idx, data_point in enumerate(data_points_without_cite_number)
        ]

        yield ChatCompletionDataPoints(data_points=data_points)

        response_generator_input = ResponseGeneratorInput(
            model=response_generator_model,
            messages=messages.root,
            attachments=[],
            max_attachment_token=input.tenant.max_attachment_token,
            data_points_from_internal=[data_point for data_point in data_points if data_point.type == Type.INTERNAL],
            data_points_from_web=[],
            data_points_from_question_answer=[
                data_point for data_point in data_points if data_point.type == Type.QUESTION_ANSWER
            ],
            data_points_from_url=[],
            tenant_name=input.tenant.name.value,
            response_system_prompt=bot.response_system_prompt,
            response_system_prompt_hidden=bot.response_system_prompt_hidden,
            terms_dict=terms_dict,
            approach=bot.approach,
        )
        if bot.approach == Approach.CUSTOM_GPT:
            response_generator_output = self.llm_service.generate_response_without_internal_data(
                inputs=response_generator_input,
            )
        elif bot.approach == Approach.NEOLLM:
            response_generator_output = self.llm_service.generate_response_with_internal_data(
                inputs=response_generator_input,
            )
        else:
            raise BadRequest("Invalid approach")

        answer = ""
        used_data_points = []
        for item in response_generator_output:
            if isinstance(item, str):
                answer += item
                yield ChatCompletionAnswer(answer=chat_completion_domain.Content(root=answer))
            if isinstance(item, list) and all(isinstance(i, ChatCompletionDataPoint) for i in item):
                used_data_points = item

        token_count = self._calculate_token_count(
            response_system_prompt=bot.response_system_prompt,
            response_system_prompt_hidden=bot.response_system_prompt_hidden,
            use_query_generator=use_query_generator,
            terms_dict=terms_dict,
            used_data_points=used_data_points,
            history=messages,
            answer=answer,
            model_name=response_generator_model,
        )

        chat_completion.update(
            chat_completion_domain.ChatCompletionForUpdate(
                messages=messages,
                answer=chat_completion_domain.Content(root=answer),
                token_count=token_count,
                data_points=data_points,
            )
        )
        self.chat_completion_repo.update(api_key_id=api_key.id, chat_completion=chat_completion)
        return self.chat_completion_repo.bulk_create_data_points(
            chat_completion_id=chat_completion.id,
            chat_completion_data_points=chat_completion.data_points,
        )

    def _get_bot_with_api_keys_list(
        self, bot_id: bot_domain.Id | None, api_key_id: api_key_domain.Id | None, tenant_id: tenant_domain.Id
    ) -> tuple[list[BotWithApiKeys], list[api_key_domain.Id]]:
        # テナントに紐づく全ボットIDとAPIキーIDを取得
        tenant_bots = self.bot_repo.find_all_by_tenant_id(tenant_id=tenant_id, include_deleted=True)
        tenant_bot_ids = [bot.id for bot in tenant_bots]

        if bot_id is not None:
            if bot_id not in tenant_bot_ids:
                raise NotFound("アシスタントが見つかりませんでした")

            bot = self.bot_repo.find_by_id(bot_id, include_deleted=True)
            api_keys = (
                [self.api_key_repo.find_by_id_and_bot_id(api_key_id, bot_id, include_deleted=True)]
                if api_key_id is not None
                else self.api_key_repo.find_by_bot_ids([bot_id], include_deleted=True)
            )
            bot_with_api_keys_list = [BotWithApiKeys(bot=bot, api_keys=api_keys)]
            api_key_ids = [api_key.id for api_key in api_keys]
            return bot_with_api_keys_list, api_key_ids

        if api_key_id is None:
            api_keys = self.api_key_repo.find_by_bot_ids(tenant_bot_ids, include_deleted=True)
            bot_with_api_keys_list = [BotWithApiKeys(bot=bot, api_keys=api_keys) for bot in tenant_bots]
            api_key_ids = [api_key.id for api_key in api_keys]
            return bot_with_api_keys_list, api_key_ids

        raise BadRequest("不正なリクエストです")

    def get_chat_completions_for_download(
        self,
        bot_id: bot_domain.Id | None,
        api_key_id: api_key_domain.Id | None,
        start_date_time: datetime,
        end_date_time: datetime,
        tenant_id: tenant_domain.Id,
    ) -> list[ChatCompletionWithBotAndApiKey]:
        # テナントに紐づく全ボットIDとAPIキーIDを取得

        bot_with_api_keys_list, api_key_ids = self._get_bot_with_api_keys_list(bot_id, api_key_id, tenant_id)
        # 対話データの検索と返却
        chat_completions = self.chat_completion_repo.find_by_api_key_ids_and_date(
            api_key_ids=api_key_ids,
            start_date_time=start_date_time,
            end_date_time=end_date_time,
        )

        return [
            ChatCompletionWithBotAndApiKey.from_chat_completion_and_bot_with_api_keys_list(
                chat_completion, bot_with_api_keys_list
            )
            for chat_completion in chat_completions
        ]

    def create_chat_completion_export(
        self,
        tenant_id: tenant_domain.Id,
        chat_completion_export_for_create: chat_completion_export_domain.ChatCompletionExportForCreate,
    ) -> chat_completion_export_domain.ChatCompletionExportWithUser:
        self._get_bot_with_api_keys_list(
            bot_id=chat_completion_export_for_create.target_bot_id,
            api_key_id=chat_completion_export_for_create.target_api_key_id,
            tenant_id=tenant_id,
        )

        # init
        chat_completion_export = self.chat_completion_export_repo.create(chat_completion_export_for_create)

        # send message to create chat completion export queue
        self.queue_storage_service.send_message_to_create_chat_completion_export_queue(
            tenant_id=tenant_id, chat_completion_export_id=chat_completion_export.id
        )

        return chat_completion_export

    def get_chat_completion_exports_with_user(
        self,
        tenant_id: tenant_domain.Id,
    ) -> list[chat_completion_export_domain.ChatCompletionExportWithUser]:
        return self.chat_completion_export_repo.find_with_user_by_tenant_id(tenant_id=tenant_id)

    def delete_chat_completion_exports(
        self, tenant_id: tenant_domain.Id, chat_completion_export_ids: list[chat_completion_export_domain.Id]
    ) -> None:
        tenant = self.tenant_repo.find_by_id(tenant_id)

        chat_completion_exports = self.chat_completion_export_repo.find_by_ids_and_tenant_id(
            tenant_id, chat_completion_export_ids
        )
        for chat_completion_export in chat_completion_exports:
            self.blob_storage_service.delete_blob_export(tenant.container_name, chat_completion_export.blob_path)

        self.chat_completion_export_repo.delete_by_ids_and_tenant_id(tenant_id, chat_completion_export_ids)

    def get_chat_completion_export_signed_url(
        self, tenant: tenant_domain.Tenant, chat_completion_export_id: chat_completion_export_domain.Id
    ) -> chat_completion_export_domain.SignedUrl:
        chat_completion_export = self.chat_completion_export_repo.find_by_id(
            tenant_id=tenant.id, id=chat_completion_export_id
        )

        return self.blob_storage_service.create_blob_chat_completion_sas_url(
            container_name=tenant.container_name, blob_path=chat_completion_export.blob_path
        )

    def update_chat_completion_feedback_evaluation(self, input: UpdateChatCompletionFeedbackEvaluationInput) -> None:
        self.chat_completion_repo.update_chat_completion_feedback_evaluation(id=input.id, evaluation=input.evaluation)

    def update_chat_completion_feedback_comment(self, input: UpdateChatCompletionFeedbackCommentInput) -> None:
        self.chat_completion_repo.update_chat_completion_feedback_comment(id=input.id, comment=input.comment)

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Callable, Generator, Optional

from injector import inject

from api.domain.models import (
    attachment as attachment_domain,
    bot as bot_domain,
    conversation as conversation_domain,
    conversation_export as conversation_export_domain,
    document as document_domain,
    document_folder as document_folder_domain,
    llm as llm_domain,
    metering as metering_domain,
    tenant as tenant_domain,
    term as term_domain,
    user as user_domain,
)
from api.domain.models.attachment.content import BlobContent
from api.domain.models.bot import Approach, SearchMethod
from api.domain.models.bot.max_conversation_turns import MaxConversationTurns
from api.domain.models.bot.response_system_prompt import ResponseSystemPrompt, ResponseSystemPromptHidden
from api.domain.models.conversation import (
    SensitiveContent,
    SensitiveContentType,
    conversation_data_point as conversation_data_point_domain,
    conversation_turn as conversation_turn_domain,
)
from api.domain.models.conversation.image_url import ImageUrl
from api.domain.models.data_point import CiteNumber, DataPoint, DataPointWithoutCiteNumber, Type
from api.domain.models.document import feedback as document_feedback_domain
from api.domain.models.llm import ModelName, get_lightweight_model_orders, get_response_generator_model_for_text2image
from api.domain.models.query.query import Queries
from api.domain.models.storage import ContainerName
from api.domain.models.term import TermsDict
from api.domain.models.text_2_image_model.model import Text2ImageModelName
from api.domain.models.token import Token, TokenCount, TokenSet
from api.domain.services.ai_vision import IAiVisionService
from api.domain.services.bing_search.bing_search import IBingSearchService
from api.domain.services.blob_storage import IBlobStorageService
from api.domain.services.cognitive_search import ICognitiveSearchService
from api.domain.services.document_intelligence import IDocumentIntelligenceService
from api.domain.services.llm import (
    ILLMService,
    QueryGeneratorInput,
    ResponseGeneratorInput,
    ResponseGeneratorOutputToken,
    ResponseGeneratorStreamOutput,
)
from api.domain.services.llm.llm import (
    Dalle3ResponseGeneratorInput,
    QueryGeneratorOutput,
    UrsaQuestionGeneratorInput,
    UrsaResponseGeneratorInput,
)
from api.domain.services.queue_storage.queue_storage import IQueueStorageService
from api.domain.services.web_scraping import IWebScrapingService
from api.libs.blob_content import split_pdf_at_page
from api.libs.exceptions import BadRequest, HTTPException, NotFound
from api.libs.feature_flag import get_feature_flag
from api.libs.logging import get_logger

from .types import (
    ConversationAttachment,
    ConversationOutputAnswer,
    ConversationOutputDataPoints,
    ConversationOutputEvent,
    ConversationOutputFollowUpQuestions,
    ConversationOutputImageUrl,
    ConversationOutputQuery,
    ConversationOutputToken,
    CreateConversationInput,
    CreateConversationOutput,
    CreateConversationOutputStream,
    CreateOrUpdateConversationTurnFeedbackCommentInput,
    GetConversationsByUserIdInput,
    PreviewConversationInput,
    PreviewConversationOutput,
    UpdateConversationEvaluationInput,
    UpdateConversationInput,
)

MAX_ATTACHMENT_STRING_LENGTH = 8000
IMAGE_GENERATOR_TOKEN = 3000
QUERY_GENERATOR_TOKEN = 500
RESPONSE_GENERATOR_TOKEN = 200
FOLLOW_UP_QUESTION_TOKEN = 300
DEFAULT_DOCUMENT_LIMIT = 5
DOCUMENT_INTELLIGENCE_MIN_PIXELS = 50
DOCUMENT_INTELLIGENCE_MAX_PIXELS = 10000


class IConversationUseCase(ABC):
    @abstractmethod
    def create_conversation(
        self,
        input: CreateConversationInput,
    ) -> CreateConversationOutput:
        pass

    @abstractmethod
    def create_conversation_stream(
        self,
        input: CreateConversationInput,
    ) -> CreateConversationOutputStream:
        pass

    @abstractmethod
    def get_conversations_for_download(
        self,
        bot_id: Optional[bot_domain.Id],
        user_id: Optional[user_domain.Id],
        start_date_time: datetime,
        end_date_time: datetime,
        tenant_id: tenant_domain.Id,
    ) -> list[conversation_turn_domain.ConversationTurnWithUserAndBot]:
        pass

    @abstractmethod
    def create_conversation_export(
        self,
        tenant_id: tenant_domain.Id,
        conversation_export_for_create: conversation_export_domain.ConversationExportForCreate,
    ) -> None:
        pass

    @abstractmethod
    def create_conversation_title(
        self,
        tenant: tenant_domain.Tenant,
        bot_id: bot_domain.Id,
        conversation_id: conversation_domain.Id,
    ) -> conversation_domain.Title:
        pass

    @abstractmethod
    def get_conversations_by_user_id(
        self, input: GetConversationsByUserIdInput
    ) -> list[conversation_domain.Conversation]:
        pass

    @abstractmethod
    def get_conversation_by_id(
        self, conversation_id: conversation_domain.Id, user_id: user_domain.Id
    ) -> conversation_domain.ConversationWithAttachments:
        pass

    @abstractmethod
    def validate_conversation(self, question: conversation_turn_domain.UserInput) -> conversation_domain.Validation:
        pass

    @abstractmethod
    def update_conversation(self, input: UpdateConversationInput) -> None:
        pass

    @abstractmethod
    def update_evaluation(self, input: UpdateConversationEvaluationInput) -> None:
        pass

    @abstractmethod
    def save_comment(
        self,
        input: CreateOrUpdateConversationTurnFeedbackCommentInput,
    ) -> None:
        pass

    @abstractmethod
    def preview_conversation(
        self,
        input: PreviewConversationInput,
    ) -> PreviewConversationOutput:
        pass

    @abstractmethod
    def get_data_points_with_document_feedback_summary(
        self,
        user_id: user_domain.Id,
        conversation_id: conversation_domain.Id,
        conversation_turn_id: conversation_turn_domain.Id,
    ) -> list[conversation_data_point_domain.ConversationDataPointWithDocumentFeedbackSummary]:
        pass

    @abstractmethod
    def get_conversation_export_with_user(
        self,
        tenant_id: tenant_domain.Id,
    ) -> list[conversation_export_domain.ConversationExportWithUser]:
        pass

    @abstractmethod
    def delete_conversation_exports(
        self, tenant_id: tenant_domain.Id, conversation_export_ids: list[conversation_export_domain.Id]
    ) -> None:
        pass

    @abstractmethod
    def get_conversation_export_signed_url(
        self, tenant: tenant_domain.Tenant, conversation_export_id: conversation_export_domain.Id
    ) -> conversation_export_domain.SignedUrl:
        pass


class ConversationUseCase(IConversationUseCase):
    @inject
    def __init__(
        self,
        tenant_repo: tenant_domain.ITenantRepository,
        bot_repo: bot_domain.IBotRepository,
        document_folder_repo: document_folder_domain.IDocumentFolderRepository,
        document_repo: document_domain.IDocumentRepository,
        term_repo: term_domain.ITermV2Repository,
        conversation_repo: conversation_domain.IConversationRepository,
        conversation_export_repo: conversation_export_domain.IConversationExportRepository,
        user_repo: user_domain.IUserRepository,
        attachment_repo: attachment_domain.IAttachmentRepository,
        metering_repo: metering_domain.IMeteringRepository,
        blob_storage_service: IBlobStorageService,
        llm_service: ILLMService,
        document_intelligence_service: IDocumentIntelligenceService,
        ai_vision_service: IAiVisionService,
        bing_search_service: IBingSearchService,
        cognitive_search_service: ICognitiveSearchService,
        web_scraping_service: IWebScrapingService,
        queue_storage_service: IQueueStorageService,
    ):
        self.tenant_repo = tenant_repo
        self.logger = get_logger()
        self.bot_repo = bot_repo
        self.document_folder_repo = document_folder_repo
        self.document_repo = document_repo
        self.term_repo = term_repo
        self.conversation_repo = conversation_repo
        self.conversation_export_repo = conversation_export_repo
        self.user_repo = user_repo
        self.attachment_repo = attachment_repo
        self.metering_repo = metering_repo
        self.blob_storage_service = blob_storage_service
        self.llm_service = llm_service
        self.document_intelligence_service = document_intelligence_service
        self.ai_vision_service = ai_vision_service
        self.bing_search_service = bing_search_service
        self.cognitive_search_service = cognitive_search_service
        self.web_scraping_service = web_scraping_service
        self.queue_storage_service = queue_storage_service

    def _save_conversation(self, bot_id: bot_domain.Id, user_id: user_domain.Id) -> conversation_domain.Id:
        # ここでconversation_domain.Idとuser_idとbot_idを保存する
        created_conversation = self.conversation_repo.save_conversation(
            conversation_domain.ConversationForCreate(
                user_id=user_id,
                bot_id=bot_id,
            )
        )
        return created_conversation.id

    def _get_conversation_with_bot(
        self, conversation_id: conversation_domain.Id, bot_id: bot_domain.Id, user_id: user_domain.Id
    ) -> conversation_domain.ConversationWithBot:
        conversation_with_bot = self.conversation_repo.find_with_bot_by_id_and_bot_id_and_user_id(
            conversation_id, bot_id, user_id
        )
        return conversation_with_bot

    def _save_conversation_turn(
        self,
        conversation_id: conversation_domain.Id,
        question: conversation_turn_domain.UserInput,
        answer: str,
        queries: list[str],
        query_generator_model: ModelName | None,
        response_generator_model: ModelName,
        image_generator_model: Text2ImageModelName | None,
        query_input_token: int,
        query_output_token: int,
        response_input_token: int,
        response_output_token: int,
        token_count: TokenCount,
        data_points: list[DataPoint],
        document_folder: document_folder_domain.DocumentFolder | None,
    ) -> conversation_turn_domain.Id:
        conversation_turn = conversation_turn_domain.ConversationTurnForCreate(
            conversation_id=conversation_id,
            user_input=question,
            bot_output=conversation_turn_domain.BotOutput(root=answer),
            queries=[conversation_turn_domain.Query(root=query) for query in queries],
            token_set=TokenSet(
                query_input_token=Token(root=query_input_token),
                query_output_token=Token(root=query_output_token),
                response_input_token=Token(root=response_input_token),
                response_output_token=Token(root=response_output_token),
            ),
            token_count=token_count,
            query_generator_model=query_generator_model,
            response_generator_model=response_generator_model,
            image_generator_model=image_generator_model,
            document_folder=document_folder,
        )
        # 空のリストを初期化
        conversation_data_points: list[conversation_data_point_domain.ConversationDataPointForCreate] = [
            conversation_data_point_domain.ConversationDataPointForCreate(
                turn_id=conversation_turn.id,
                content=data_point.content,
                chunk_name=data_point.chunk_name,
                cite_number=data_point.cite_number,
                page_number=data_point.page_number,
                blob_path=data_point.blob_path,
                type=data_point.type,
                url=data_point.url,
                additional_info=data_point.additional_info,
                document_id=data_point.document_id,
                question_answer_id=data_point.question_answer_id,
            )
            for data_point in data_points
        ]

        created_conversation_turn = self.conversation_repo.save_conversation_turn(
            conversation_turn, conversation_data_points
        )

        self.conversation_repo.update_conversation_timestamp(conversation_id)

        return created_conversation_turn.id

    def _validate_search_conversation(self, tenant: tenant_domain.Tenant, bot: bot_domain.Bot) -> None:
        approach = bot.approach
        search_method = bot.search_method
        if approach.value != Approach.URSA and search_method not in [SearchMethod.URSA, SearchMethod.URSA_SEMANTIC]:
            return

        URSA_TENANT_FLAG_KEY = "ursa-tenant"

        flag = get_feature_flag(URSA_TENANT_FLAG_KEY, tenant.id, tenant.name)
        if not flag:
            raise Exception("Feature flag is not enabled")

    def _save_page_count(
        self,
        tenant_id: tenant_domain.Id,
        tenant_name: tenant_domain.Name,
        bot_id: bot_domain.Id,
        pdf_parser: llm_domain.PdfParser,
        page_count: metering_domain.Quantity,
    ):
        FLAG = "tmp-ocr-to-token"
        flag = get_feature_flag(FLAG, tenant_id, tenant_name)

        self.metering_repo.create_pdf_parser_count(
            metering_domain.PdfParserMeterForCreate(
                tenant_id=tenant_id,
                bot_id=bot_id,
                type=(
                    metering_domain.PDFParserCountType.from_pdf_parser_v2(pdf_parser)
                    if flag
                    else metering_domain.PDFParserCountType.from_pdf_parser(pdf_parser)
                ),
                quantity=page_count,
            )
        )

    def _parse_pdf(
        self,
        tenant: tenant_domain.Tenant,
        bot_id: bot_domain.Id,
        blob_content: BlobContent,
        pdf_parser: llm_domain.PdfParser,
    ) -> attachment_domain.Content:
        if pdf_parser == llm_domain.PdfParser.PYPDF:
            return blob_content.parse_pdf_file_by_pypdf()

        MAX_PAGES_FOR_INTELLIGENCE = 30
        content_page_count = blob_content.count_pages()

        parsers: dict[
            llm_domain.PdfParser, Callable[[BlobContent], tuple[attachment_domain.Content, metering_domain.Quantity]]
        ] = {
            llm_domain.PdfParser.DOCUMENT_INTELLIGENCE: lambda blob_content: self.document_intelligence_service.parse_pdf(
                blob_content
            ),
            llm_domain.PdfParser.LLM_DOCUMENT_READER: lambda blob_content: self.document_intelligence_service.parse_pdf(
                blob_content
            ),
            llm_domain.PdfParser.AI_VISION: lambda blob_content: self.ai_vision_service.parse_pdf_by_ai_vision(
                blob_content
            ),
        }

        parser = parsers.get(pdf_parser)
        if parser is None:
            raise BadRequest("ドキュメント読み取りオプションが不正です。")

        if content_page_count.root > MAX_PAGES_FOR_INTELLIGENCE:
            # ページ数が多い場合は分割して処理
            first_half, second_half = split_pdf_at_page(blob_content, MAX_PAGES_FOR_INTELLIGENCE)
            # 前半部分はDocument Intelligenceで処理
            first_content, page_count = parser(first_half)
            # 後半部分はPyPDFで処理
            second_content = second_half.parse_pdf_file_by_pypdf()
            content = first_content.merge(second_content)
        else:
            content, page_count = parser(blob_content)

        self._save_page_count(tenant.id, tenant.name, bot_id, pdf_parser, page_count)
        return content

    def _get_attachment_for_conversation(
        self,
        tenant: tenant_domain.Tenant,
        bot_id: bot_domain.Id,
        container_name: ContainerName,
        pdf_parser: llm_domain.PdfParser,
        attachment_id: attachment_domain.Id,
    ) -> attachment_domain.AttachmentForConversation:
        attachment = self.attachment_repo.find_by_id(attachment_id)

        blob_content = self.blob_storage_service.get_attachment_blob_content(
            container_name=container_name, bot_id=bot_id, blob_name=attachment.blob_name
        )
        extension = attachment.file_extension

        if extension.is_image():
            if pdf_parser not in [
                llm_domain.PdfParser.DOCUMENT_INTELLIGENCE,
                llm_domain.PdfParser.LLM_DOCUMENT_READER,
            ]:
                raise BadRequest("ドキュメント読み取りオプションが不正です。")
            blob_content.resize_image(
                min_size=(DOCUMENT_INTELLIGENCE_MIN_PIXELS, DOCUMENT_INTELLIGENCE_MIN_PIXELS),
                max_size=(DOCUMENT_INTELLIGENCE_MAX_PIXELS, DOCUMENT_INTELLIGENCE_MAX_PIXELS),
                format_=extension.to_pil_image_format(),
            )
            content, page_count = self.document_intelligence_service.parse_pdf(blob_content)
            self._save_page_count(tenant.id, tenant.name, bot_id, pdf_parser, page_count)
            return attachment_domain.AttachmentForConversation(
                name=attachment.name,
                content=content,
            )

        parsers = {
            attachment_domain.FileExtension.DOCX: lambda: blob_content.parse_docx_file(),
            attachment_domain.FileExtension.XLSX: lambda: blob_content.parse_xlsx_file(),
            attachment_domain.FileExtension.PPTX: lambda: blob_content.parse_pptx_file(),
        }

        if extension == attachment_domain.FileExtension.PDF:
            content = self._parse_pdf(
                tenant=tenant,
                bot_id=bot_id,
                blob_content=blob_content,
                pdf_parser=pdf_parser,
            )
        elif extension in parsers:
            content = parsers[extension]()
        else:
            raise BadRequest("ファイルの拡張子が不正です。")

        return attachment_domain.AttachmentForConversation(
            name=attachment.name,
            content=content,
        )

    def _update_attachments(
        self, attachments: list[ConversationAttachment], conversation_turn_id: conversation_turn_domain.Id
    ) -> None:
        ids = [attachment.attachment_id for attachment in attachments]
        self.attachment_repo.update_conversation_turn_ids(ids, conversation_turn_id)

    def _calculate_token_count(
        self,
        response_system_prompt: ResponseSystemPrompt | None,
        response_system_prompt_hidden: ResponseSystemPromptHidden | None,
        history: list[conversation_turn_domain.Turn],
        answer_tokens: Token,
        attachments: list[dict[str, attachment_domain.AttachmentForConversation]],
        data_points: list[DataPoint],
        terms_dict: TermsDict,
        use_query_generator: bool,
        use_image_generator: bool,
        model_name: ModelName,
        is_follow_up_questions_generated: bool = False,
    ) -> TokenCount:
        tokens = Token(root=0)

        # カスタムのプロンプトのトークン数
        if response_system_prompt is not None:
            tokens += Token.from_string(response_system_prompt.root)
        if response_system_prompt_hidden is not None:
            tokens += Token.from_string(response_system_prompt_hidden.root)

        # これまでの会話のトークン数
        for turn in history:
            tokens += Token.from_string(turn.user.root)
            if turn.bot is not None:
                tokens += Token.from_string(turn.bot.root)
        # ボットの出力のトークン数
        tokens += answer_tokens

        # attachmentsのトークン数
        for attachment in attachments:
            if "user" in attachment:
                tokens += Token.from_string(attachment["user"].name.root)
                content_tokens = Token.from_string(attachment["user"].content.root)
                tokens += Token(root=min(content_tokens.root, MAX_ATTACHMENT_STRING_LENGTH))

        # data_pointのトークン数
        for data_point in data_points:
            tokens += Token.from_string(data_point.content.root)

        # termsのトークン数
        for key, value in terms_dict.root.items():
            tokens += Token.from_string(key)
            tokens += Token.from_string(value)

        # 固定値のトークン数
        if use_query_generator:
            tokens += Token(root=QUERY_GENERATOR_TOKEN)
            tokens += Token(root=RESPONSE_GENERATOR_TOKEN)
        else:
            tokens += Token(root=RESPONSE_GENERATOR_TOKEN)

        # モデルによるトークン数の計算
        total_token = TokenCount.from_token(tokens, model_name, False)

        # 画像生成のトークン数
        if use_image_generator:
            total_token += TokenCount(root=IMAGE_GENERATOR_TOKEN)

        if is_follow_up_questions_generated:
            total_token += TokenCount(root=FOLLOW_UP_QUESTION_TOKEN)

        return total_token

    def _create_search_filter(
        self,
        bot: bot_domain.Bot,
        document_folder_with_descendants: document_folder_domain.DocumentFolderWithDescendants | None,
    ) -> str:
        filters: list[str] = []
        if bot.search_method not in {SearchMethod.URSA, SearchMethod.URSA_SEMANTIC}:
            filters.append(bot.id_filter_for_search_index())
        if document_folder_with_descendants is not None:
            filters.append(document_folder_with_descendants.id_filter_for_search_index())
        return " and ".join(filters)

    def create_conversation(
        self,
        input: CreateConversationInput,
    ) -> CreateConversationOutput:
        it = self.create_conversation_stream(input)
        conversation_id = None
        conversation_turn_id = None
        queries = []
        image_url = ImageUrl(root="")
        data_points = []
        answer = ""
        follow_up_questions = []
        for item in it:
            if isinstance(item, conversation_domain.Id):
                conversation_id = item
            if isinstance(item, conversation_turn_domain.Id):
                conversation_turn_id = item
            if isinstance(item, ConversationOutputQuery):
                queries = item.query
            if isinstance(item, ConversationOutputImageUrl):
                image_url = item.image_url
            if isinstance(item, ConversationOutputDataPoints):
                data_points = item.data_points
            if isinstance(item, ConversationOutputAnswer):
                answer += item.answer
            if isinstance(item, ConversationOutputFollowUpQuestions):
                follow_up_questions = item.follow_up_questions
        if conversation_id is None or conversation_turn_id is None:
            raise Exception("conversation_id or conversation_turn_id is not set")
        return CreateConversationOutput(
            conversation_id=conversation_id,
            conversation_turn_id=conversation_turn_id,
            data_points=data_points,
            answer=answer,
            query=queries,
            follow_up_questions=follow_up_questions,
            image_url=image_url,
        )

    def _generate_query(self, bot: bot_domain.Bot, query_generator_input: QueryGeneratorInput):
        if bot.approach == Approach.TEXT_2_IMAGE:
            return self.llm_service.generate_query_for_dalle3(inputs=query_generator_input)
        if bot.approach == Approach.URSA:
            return self.llm_service.generate_ursa_query(inputs=query_generator_input)
        if bot.approach not in [Approach.TEXT_2_IMAGE, Approach.URSA]:
            return self.llm_service.generate_query(inputs=query_generator_input)
        raise Exception("Invalid approach")

    def create_conversation_stream(
        self,
        input: CreateConversationInput,
    ) -> CreateConversationOutputStream:
        yield ConversationOutputEvent(event=conversation_domain.Event.CONVERSATION_STARTED)

        conversation_id = input.conversation_id
        if conversation_id is None:
            conversation_id = self._save_conversation(input.bot_id, input.user_id)
        yield conversation_id

        # バリデーションしてbotを取得する
        conversation = self._get_conversation_with_bot(conversation_id, input.bot_id, input.user_id)
        bot = conversation.bot

        # 使用できるモデルかどうかを確認する
        bot.validate_allowed_model_families(input.tenant.allowed_model_families)

        if (
            not bot.enable_web_browsing_with_tenant_setting(input.tenant.enable_basic_ai_web_browsing)
            and input.use_web_browsing.root
        ):
            raise BadRequest("Web検索が有効になっていません。")

        # 資料検索の場合は、検索対象のbotかどうかを確認する
        self._validate_search_conversation(input.tenant, bot)

        # モデルの取得
        lightweight_models = get_lightweight_model_orders(
            allow_foreign_region=input.tenant.allow_foreign_region,
            platforms=[platform.root for platform in input.tenant.additional_platforms.root],
        )

        response_generator_model = (
            bot.response_generator_model_family.to_model(
                allow_foreign_region=input.tenant.allow_foreign_region,
                additional_platforms=[platform.root for platform in input.tenant.additional_platforms.root],
            )
            if bot.approach != Approach.TEXT_2_IMAGE
            else get_response_generator_model_for_text2image(
                allow_foreign_region=input.tenant.allow_foreign_region,
                platforms=[platform.root for platform in input.tenant.additional_platforms.root],
            )
        )
        image_generator_model = (
            bot.image_generator_model_family.to_model(input.tenant.allow_foreign_region)
            if bot.image_generator_model_family is not None
            else None
        )

        # 用語集の取得
        terms = self.term_repo.find_by_bot_id(input.bot_id)

        # 添付ファイルの取得
        attachments: list[dict[str, attachment_domain.AttachmentForConversation]] = []
        for d in input.attachments:
            try:
                pdf_parser = llm_domain.PdfParser.PYPDF
                if bot.approach == Approach.CHAT_GPT_DEFAULT:
                    pdf_parser = input.tenant.basic_ai_pdf_parser.to_bot_pdf_parser()
                elif bot.pdf_parser is not None:
                    pdf_parser = bot.pdf_parser

                attachment_blob = self._get_attachment_for_conversation(
                    tenant=input.tenant,
                    bot_id=input.bot_id,
                    container_name=input.tenant.container_name,
                    pdf_parser=pdf_parser,
                    attachment_id=d.attachment_id,
                )
            except NotFound:
                # attachmentがBlob Storageに存在しない場合はスキップする
                continue
            if d.from_ == "bot":
                attachments.append({"bot": attachment_blob})
            if d.from_ == "user":
                attachments.append({"user": attachment_blob})

        # 今までの会話を取得して、最大会話数を超えている場合は切り詰める
        turns = conversation_turn_domain.Turns(
            root=[conversation_turn.to_turn() for conversation_turn in conversation.turns]
        ).cut_by_max_ceonversartion_turns(
            input.tenant.basic_ai_max_conversation_turns
            if bot.approach == Approach.CHAT_GPT_DEFAULT
            else bot.max_conversation_turns
        )
        # ユーザーの質問を追加
        turns.add_turn(
            conversation_turn_domain.Turn(
                user=conversation_turn_domain.Message(root=input.question.root),
                bot=None,
            )
        )
        messages = turns.to_messages()
        # if Webスクレイピング
        urls: list[str] = []
        data_points_from_url: list[DataPoint] = []

        FLAG_KEY = "tmp-web-scraping"
        flag = get_feature_flag(FLAG_KEY, input.tenant.id, input.tenant.name)
        if (
            input.tenant.enable_url_scraping.root
            and flag
            and bot.enable_web_browsing_with_tenant_setting(input.tenant.enable_basic_ai_web_browsing)
        ):
            urls.extend(self.web_scraping_service.find_url_from_text(input.question.root))
            if urls:
                url_data_points = self.web_scraping_service.web_search_from_url(urls)
                data_points_from_url.extend(url_data_points)

        # クエリ生成
        queries = []
        query_generator_output = None
        query_generator_model = None

        if (
            bot.use_query_generator(input.use_web_browsing, input.tenant.enable_basic_ai_web_browsing)
            and len(urls) == 0
        ):
            for qgm in lightweight_models:
                query_generator_input = QueryGeneratorInput(
                    model=qgm,
                    messages=messages,
                    tenant_name=input.tenant.name,
                    query_system_prompt=bot.query_system_prompt,
                )
                yield ConversationOutputEvent(
                    event=(
                        conversation_domain.Event.PROMPT_GENERATION_STARTED
                        if bot.approach == Approach.TEXT_2_IMAGE
                        else conversation_domain.Event.QUERY_GENERATION_STARTED
                    )
                )
                try:
                    query_generator_output = self._generate_query(bot, query_generator_input)
                    queries = query_generator_output.queries.to_string_list()
                    query_generator_model = qgm
                    yield ConversationOutputQuery(
                        query=[queries[0]] if bot.approach == Approach.TEXT_2_IMAGE else queries
                    )
                    yield ConversationOutputEvent(
                        event=(
                            conversation_domain.Event.PROMPT_GENERATION_COMPLETED
                            if bot.approach == Approach.TEXT_2_IMAGE
                            else conversation_domain.Event.QUERY_GENERATION_COMPLETED
                        )
                    )
                    break
                except Exception as e:
                    msg = f"Failed to generate query with model {qgm.value}"
                    if isinstance(e, HTTPException) and e.status_code >= 400 and e.status_code < 500:
                        self.logger.warning(msg, exc_info=e)
                    else:
                        self.logger.error(msg, exc_info=e)
                    continue

            if query_generator_output is None:
                query_generator_output = QueryGeneratorOutput(
                    queries=Queries.from_list([input.question.root]),
                    input_token=0,
                    output_token=0,
                )

        # if 画像生成
        if bot.approach == Approach.TEXT_2_IMAGE and bot.image_generator_model_family is not None:
            yield ConversationOutputEvent(event=conversation_domain.Event.IMAGE_GENERATION_STARTED)
            image_url = self.llm_service.generate_image(
                model=bot.image_generator_model_family.to_model(input.tenant.allow_foreign_region), prompt=queries[0]
            )
            yield ConversationOutputImageUrl(image_url=image_url)
            yield ConversationOutputEvent(event=conversation_domain.Event.IMAGE_GENERATION_COMPLETED)

        # 用語集がある場合の検索クエリアップデート
        search_queries, terms_dict = self.llm_service.update_query_with_terms(
            queries=query_generator_output.queries if query_generator_output is not None else Queries.from_list([]),
            terms=terms,
        )

        # retrieve
        internal_data = bot.approach in [Approach.NEOLLM, Approach.URSA]
        data_points_without_cite_number: list[DataPointWithoutCiteNumber] = []

        # if ブラウジング
        if (
            bot.enable_web_browsing_with_tenant_setting(input.tenant.enable_basic_ai_web_browsing)
            and input.use_web_browsing.root
            and not urls
        ):
            yield ConversationOutputEvent(event=conversation_domain.Event.WEB_DOCUMENTS_RETRIEVAL_STARTED)

            try:
                web_data_points = self.bing_search_service.search_web_documents(queries=search_queries)
                data_points_without_cite_number.extend(web_data_points)
            except Exception as e:
                # Web検索が失敗した場合はログを出力して続行する
                self.logger.error("Failed to search web document", exc_info=e)

            yield ConversationOutputEvent(event=conversation_domain.Event.WEB_DOCUMENTS_RETRIEVAL_COMPLETED)

        # ドキュメントのためにフォルダを取得
        document_folder_with_descendants = None
        if input.document_folder_id is not None:
            document_folder_with_descendants = self.document_folder_repo.find_with_descendants_by_id_and_bot_id(
                input.document_folder_id, bot.id
            )

        # if ドキュメント
        if internal_data:
            yield ConversationOutputEvent(event=conversation_domain.Event.INTERNAL_DOCUMENTS_RETRIEVAL_STARTED)

            embeddings = []
            if bot.search_method is not None and bot.search_method.should_create_embeddings():
                embeddings = self.llm_service.generate_embeddings(search_queries.to_string(delimiter=" "))
            endpoint = (
                input.tenant.search_service_endpoint
                if bot.search_method not in [SearchMethod.URSA, SearchMethod.URSA_SEMANTIC]
                else bot.search_service_endpoint
            )
            if not endpoint:
                raise Exception("search_service_endpoint is required")
            index_name = (
                input.tenant.index_name
                if bot.search_method not in [SearchMethod.URSA, SearchMethod.URSA_SEMANTIC]
                else bot.index_name
            )
            if not index_name:
                raise Exception("index_name is required")

            filter_ = self._create_search_filter(bot, document_folder_with_descendants)

            internal_data_points = self.cognitive_search_service.search_documents(
                endpoint=endpoint,
                index_name=index_name,
                queries=search_queries,
                document_limit=bot.document_limit,
                filter=filter_,
                search_method=bot.search_method or SearchMethod.BM25,
                embeddings=embeddings,
                additional_kwargs=(
                    query_generator_output.additional_kwargs if query_generator_output is not None else {}
                ),
            )
            data_points_without_cite_number.extend(internal_data_points)

            yield ConversationOutputEvent(event=conversation_domain.Event.INTERNAL_DOCUMENTS_RETRIEVAL_COMPLETED)

        data_point_type_order = [Type.INTERNAL, Type.QUESTION_ANSWER, Type.WEB]
        data_points_without_cite_number = sorted(
            data_points_without_cite_number, key=lambda dp: data_point_type_order.index(dp.type)
        )

        # cite_numberを通し番号でふる
        data_points: list[DataPoint] = []
        for i, data_point in enumerate(data_points_without_cite_number):
            data_points.append(
                DataPoint(
                    content=data_point.content,
                    page_number=data_point.page_number,
                    chunk_name=data_point.chunk_name,
                    blob_path=data_point.blob_path,
                    type=data_point.type,
                    url=data_point.url,
                    document_id=data_point.document_id,
                    question_answer_id=data_point.question_answer_id,
                    additional_info=data_point.additional_info,
                    cite_number=CiteNumber(root=i + 1),
                )
            )

        yield ConversationOutputDataPoints(data_points=data_points)

        # response generator
        yield ConversationOutputEvent(event=conversation_domain.Event.RESPONSE_GENERATION_STARTED)
        response_generator_output: Generator[ResponseGeneratorStreamOutput, None, None]

        if bot.approach == Approach.TEXT_2_IMAGE:
            dalle3_response_generator_input = Dalle3ResponseGeneratorInput(
                model=response_generator_model,
                messages=messages,
                attachments=attachments,
                max_attachment_token=tenant_domain.MaxAttachmentToken(root=0),
                data_points_from_internal=[
                    data_point for data_point in data_points if data_point.type == Type.INTERNAL
                ],
                data_points_from_web=[data_point for data_point in data_points if data_point.type == Type.WEB],
                data_points_from_question_answer=[],
                data_points_from_url=data_points_from_url,
                tenant_name=input.tenant.name.value,
                response_system_prompt=bot.response_system_prompt,
                response_system_prompt_hidden=bot.response_system_prompt_hidden,
                terms_dict=terms_dict,
                approach=bot.approach,
                image_url=image_url,
            )
            response_generator_output = self.llm_service.generate_response_for_dalle3(
                inputs=dalle3_response_generator_input
            )
        else:
            response_generator_input = ResponseGeneratorInput(
                model=response_generator_model,
                messages=messages,
                attachments=attachments,
                max_attachment_token=input.tenant.max_attachment_token,
                data_points_from_internal=[
                    data_point for data_point in data_points if data_point.type == Type.INTERNAL
                ],
                data_points_from_web=[data_point for data_point in data_points if data_point.type == Type.WEB],
                data_points_from_question_answer=[
                    data_point for data_point in data_points if data_point.type == Type.QUESTION_ANSWER
                ],
                data_points_from_url=data_points_from_url,
                tenant_name=input.tenant.name.value,
                response_system_prompt=bot.response_system_prompt,
                response_system_prompt_hidden=bot.response_system_prompt_hidden,
                terms_dict=terms_dict,
                approach=bot.approach,
            )
            if bot.approach in [Approach.CHAT_GPT_DEFAULT, Approach.CUSTOM_GPT]:
                response_generator_output = self.llm_service.generate_response_without_internal_data(
                    inputs=response_generator_input
                )
            elif bot.approach == Approach.NEOLLM:
                response_generator_output = self.llm_service.generate_response_with_internal_data(
                    inputs=response_generator_input
                )
            elif bot.approach == Approach.URSA:
                response_generator_output = self.llm_service.generate_ursa_response(
                    inputs=UrsaResponseGeneratorInput(
                        queries=search_queries,
                        additional_kwargs=(
                            query_generator_output.additional_kwargs if query_generator_output is not None else {}
                        ),
                    )
                )

        answer = ""
        used_data_points: list[DataPoint] = []
        response_generator_token = ResponseGeneratorOutputToken(
            input_token=0,
            output_token=0,
        )
        if bot.approach == Approach.TEXT_2_IMAGE:
            answer += image_url.to_markdown() + "\n\n"
            yield ConversationOutputAnswer(answer=answer)
        for item in response_generator_output:
            if isinstance(item, str):
                answer += item
                yield ConversationOutputAnswer(answer=item)
            if isinstance(item, list) and all(isinstance(d, DataPoint) for d in item):
                used_data_points = item
            if isinstance(item, ResponseGeneratorOutputToken):
                response_generator_token = item

        yield ConversationOutputEvent(event=conversation_domain.Event.RESPONSE_GENERATION_COMPLETED)

        # if フォローアップquestionを利用する:
        follow_up_questions = []
        if bot.enable_follow_up_questions.root:
            if bot.approach == Approach.NEOLLM and len(data_points) > 0:
                for gqm in lightweight_models:
                    try:
                        follow_up_questions = self.llm_service.generate_questions(
                            model_name=gqm,
                            data_points=data_points,
                        )
                        break
                    except Exception as e:
                        msg = f"Failed to generate question with model {gqm.value}"
                        if isinstance(e, HTTPException) and e.status_code >= 400 and e.status_code < 500:
                            self.logger.warning(msg, exc_info=e)
                        else:
                            self.logger.error(msg, exc_info=e)
                        continue
            elif bot.approach == Approach.URSA:
                follow_up_questions = self.llm_service.generate_ursa_questions(
                    inputs=UrsaQuestionGeneratorInput(
                        messages=messages,
                        queries=search_queries,
                        additional_kwargs=(
                            query_generator_output.additional_kwargs if query_generator_output is not None else {}
                        ),
                    )
                )
            yield ConversationOutputFollowUpQuestions(
                follow_up_questions=[follow_up_question.root for follow_up_question in follow_up_questions]
            )

        token = ConversationOutputToken(
            query_input_token=query_generator_output.input_token if query_generator_output is not None else 0,
            query_output_token=query_generator_output.output_token if query_generator_output is not None else 0,
            response_input_token=response_generator_token.input_token,
            response_output_token=response_generator_token.output_token,
        )

        token_count = self._calculate_token_count(
            response_system_prompt=bot.response_system_prompt,
            response_system_prompt_hidden=bot.response_system_prompt_hidden,
            history=turns.root,
            answer_tokens=(
                # o1 などの Reasoning Models は出力されない Reasoning Tokens も含めるため、response_generator_token を使う
                Token(root=response_generator_token.output_token)
                if response_generator_model.is_reasoning_model()
                else Token.from_string(answer)
            ),
            attachments=attachments,
            data_points=used_data_points,
            terms_dict=terms_dict,
            use_query_generator=bot.use_query_generator(
                input.use_web_browsing, input.tenant.enable_basic_ai_web_browsing
            ),
            use_image_generator=bot.approach == Approach.TEXT_2_IMAGE,
            model_name=response_generator_model,
            is_follow_up_questions_generated=len(follow_up_questions) > 0,
        )

        # 会話の保存
        conversation_turn_id = self._save_conversation_turn(
            conversation_id=conversation_id,
            question=input.question,
            answer=answer,
            queries=queries,
            query_generator_model=query_generator_model,
            response_generator_model=response_generator_model,
            image_generator_model=image_generator_model,
            query_input_token=token.query_input_token,
            query_output_token=token.query_output_token,
            response_input_token=token.response_input_token,
            response_output_token=token.response_output_token,
            token_count=token_count,
            data_points=data_points,
            document_folder=document_folder_with_descendants,
        )
        yield conversation_turn_id
        self._update_attachments(input.attachments, conversation_turn_id)
        yield ConversationOutputEvent(event=conversation_domain.Event.CONVERSATION_COMPLETED)

    def _preview_chat_completion_create(
        self,
        tenant_name: tenant_domain.Name,
        turns: list[conversation_turn_domain.Turn],
        approach: Approach,
        response_generator_model: ModelName,
        response_system_prompt: Optional[ResponseSystemPrompt],
    ) -> CreateConversationOutputStream:
        response_generator_input = ResponseGeneratorInput(
            model=response_generator_model,
            messages=conversation_turn_domain.Turns(root=turns)
            .cut_by_max_ceonversartion_turns(MaxConversationTurns(root=5))
            .to_messages(),
            attachments=[],
            max_attachment_token=tenant_domain.MaxAttachmentToken(root=0),
            data_points_from_internal=[],
            data_points_from_web=[],
            data_points_from_question_answer=[],
            data_points_from_url=[],
            tenant_name=tenant_name.value,
            response_system_prompt=response_system_prompt,
            response_system_prompt_hidden=None,
            terms_dict=TermsDict(),
            approach=approach,
        )
        it = self.llm_service.generate_response_without_internal_data(inputs=response_generator_input)
        for item in it:
            if isinstance(item, str):
                yield ConversationOutputAnswer(answer=item)
                continue
            if isinstance(item, list) and all(isinstance(d, DataPoint) for d in item):
                yield ConversationOutputDataPoints(data_points=item)
                continue

    def get_conversations_for_download(
        self,
        bot_id: Optional[bot_domain.Id],
        user_id: Optional[user_domain.Id],
        start_date_time: datetime,
        end_date_time: datetime,
        tenant_id: tenant_domain.Id,
    ) -> list[conversation_turn_domain.ConversationTurnWithUserAndBot]:
        # テナントに紐づく全ユーザーIDとボットIDを取得
        tenant_user_ids = [
            user.id for user in self.user_repo.find_by_tenant_id(tenant_id=tenant_id, include_deleted=True)
        ]
        tenant_bot_ids = [
            bot.id for bot in self.bot_repo.find_all_by_tenant_id(tenant_id=tenant_id, include_deleted=True)
        ]

        # IDのバリデーションと検索用IDリストの設定
        if user_id and user_id not in tenant_user_ids:
            raise ValueError("user is not found")
        if bot_id and bot_id not in tenant_bot_ids:
            raise ValueError("bot is not found")

        # 検索条件の設定
        user_ids = [user_id] if user_id else tenant_user_ids
        bot_ids = [bot_id] if bot_id else tenant_bot_ids

        # 対話データの検索と返却
        conversations = self.conversation_repo.find_conversation_turns_by_user_ids_bot_ids_and_date(
            user_ids=user_ids,
            bot_ids=bot_ids,
            start_date_time=start_date_time,
            end_date_time=end_date_time,
        )

        return conversations

    def get_conversation_export_with_user(
        self, tenant_id: tenant_domain.Id
    ) -> list[conversation_export_domain.ConversationExportWithUser]:
        return self.conversation_export_repo.find_with_user_by_tenant_id(tenant_id)

    def create_conversation_export(
        self,
        tenant_id: tenant_domain.Id,
        conversation_export_for_create: conversation_export_domain.ConversationExportForCreate,
    ) -> None:
        # validate
        # テナントに紐づく全ユーザーIDとボットIDを取得
        tenant_user_ids = [
            user.id for user in self.user_repo.find_by_tenant_id(tenant_id=tenant_id, include_deleted=True)
        ]
        tenant_bot_ids = [
            bot.id for bot in self.bot_repo.find_all_by_tenant_id(tenant_id=tenant_id, include_deleted=True)
        ]
        # IDのバリデーションと検索用IDリストの設定
        if (
            conversation_export_for_create.target_bot_id is not None
            and conversation_export_for_create.target_bot_id not in tenant_bot_ids
        ):
            raise NotFound("target bot is not found ")
        if (
            conversation_export_for_create.target_user_id is not None
            and conversation_export_for_create.target_user_id not in tenant_user_ids
        ):
            raise NotFound("terget user is not found")

        # init
        conversation_export = self.conversation_export_repo.create(conversation_export_for_create)

        # send message to create conversation export queue
        self.queue_storage_service.send_message_to_create_conversation_export_queue(
            tenant_id=tenant_id, conversation_export_id=conversation_export.id
        )

    def delete_conversation_exports(
        self, tenant_id: tenant_domain.Id, conversation_export_ids: list[conversation_export_domain.Id]
    ) -> None:
        tenant = self.tenant_repo.find_by_id(tenant_id)

        conversation_exports = self.conversation_export_repo.find_by_ids_and_tenant_id(
            tenant_id, conversation_export_ids
        )
        for conversation_export in conversation_exports:
            self.blob_storage_service.delete_blob_export(tenant.container_name, conversation_export.blob_path)

        self.conversation_export_repo.delete_by_ids_and_tenant_id(tenant_id, conversation_export_ids)

    def get_conversation_export_signed_url(
        self, tenant: tenant_domain.Tenant, conversation_export_id: conversation_export_domain.Id
    ) -> conversation_export_domain.SignedUrl:
        conversation_export = self.conversation_export_repo.find_by_id(tenant_id=tenant.id, id=conversation_export_id)

        return self.blob_storage_service.create_blob_conversation_sas_url(
            container_name=tenant.container_name, blob_path=conversation_export.blob_path
        )

    def create_conversation_title(
        self,
        tenant: tenant_domain.Tenant,
        bot_id: bot_domain.Id,
        conversation_id: conversation_domain.Id,
    ) -> conversation_domain.Title:
        turn_list = self.conversation_repo.find_turns_by_id_and_bot_id(bot_id, conversation_id)

        title = conversation_domain.Title()
        for model in get_lightweight_model_orders(
            allow_foreign_region=tenant.allow_foreign_region,
            platforms=[platform.root for platform in tenant.additional_platforms.root],
        ):
            try:
                title = self.llm_service.generate_conversation_title(model, turn_list)
                self.conversation_repo.save_conversation_title(conversation_id, title)
                break
            except Exception as e:
                msg = f"Failed to generate conversation title with model {model.value}"
                if isinstance(e, HTTPException) and e.status_code >= 400 and e.status_code < 500:
                    self.logger.warning(msg, exc_info=e)
                else:
                    self.logger.error(msg, exc_info=e)
                continue
        return title

    def get_conversations_by_user_id(
        self, input: GetConversationsByUserIdInput
    ) -> list[conversation_domain.Conversation]:
        conversations = self.conversation_repo.find_by_user_id(
            input.tenant_id,
            input.user_id,
            input.offset.root,
            input.limit.root,
        )
        return conversations

    def get_conversation_by_id(
        self, conversation_id: conversation_domain.Id, user_id: user_domain.Id
    ) -> conversation_domain.ConversationWithAttachments:
        return self.conversation_repo.find_by_id(conversation_id, user_id)

    def validate_conversation(self, question: conversation_turn_domain.UserInput) -> conversation_domain.Validation:
        sensitive_contents = []
        for content_type_str in SensitiveContentType.to_list():
            content_type = SensitiveContentType.from_value(content_type_str)
            if content_type:
                has_sensitive_content, matched_content = question.check_sensitive_contents(content_type)
                if has_sensitive_content:
                    sensitive_contents.append(SensitiveContent(type=content_type, content=matched_content))
        if len(sensitive_contents) == 0:
            return conversation_domain.Validation(
                is_valid=True,
                sensitive_contents=sensitive_contents,
            )
        return conversation_domain.Validation(
            is_valid=False,
            sensitive_contents=sensitive_contents,
        )

    def update_conversation(self, input: UpdateConversationInput) -> None:
        self.conversation_repo.update_conversation(
            id=input.conversation_id, user_id=input.user_id, title=input.title, is_archived=input.is_archived
        )
        return

    def update_evaluation(self, input: UpdateConversationEvaluationInput) -> None:
        self.conversation_repo.update_evaluation(
            id=input.conversation_id, turn_id=input.conversation_turn_id, evaluation=input.evaluation
        )
        return

    def save_comment(self, input: CreateOrUpdateConversationTurnFeedbackCommentInput) -> None:
        return self.conversation_repo.save_comment(
            conversation_id=input.conversation_id,
            conversation_turn_id=input.conversation_turn_id,
            comment=input.comment,
        )

    def preview_conversation(
        self,
        input: PreviewConversationInput,
    ) -> PreviewConversationOutput:
        out = self._preview_chat_completion_create(
            tenant_name=input.tenant.name,
            turns=input.history,
            approach=input.approach,
            response_generator_model=input.response_generator_model_family.to_model(
                input.tenant.allow_foreign_region,
                [platform.root for platform in input.tenant.additional_platforms.root],
            ),
            response_system_prompt=input.response_system_prompt,
        )

        for item in out:
            if isinstance(item, ConversationOutputDataPoints):
                yield item
                continue
            if isinstance(item, ConversationOutputAnswer):
                yield item
                continue

    def get_data_points_with_document_feedback_summary(
        self,
        user_id: user_domain.Id,
        conversation_id: conversation_domain.Id,
        conversation_turn_id: conversation_turn_domain.Id,
    ) -> list[conversation_data_point_domain.ConversationDataPointWithDocumentFeedbackSummary]:
        data_points_with_total_good = (
            self.conversation_repo.find_data_points_with_total_good_by_user_id_and_id_and_turn_id(
                user_id, conversation_id, conversation_turn_id
            )
        )

        documnt_ids = [
            data_point.document_id for data_point in data_points_with_total_good if data_point.document_id is not None
        ]

        user_document_feedbacks = self.document_repo.find_feedbacks_by_ids_and_user_id(documnt_ids, user_id)

        document_id_to_feedback_mapping = {
            feedback.document_id.value: feedback.evaluation for feedback in user_document_feedbacks
        }

        cdps_with_document_feedback_summary = []
        for data_point in data_points_with_total_good:
            if data_point.document_id is None:
                cdps_with_document_feedback_summary.append(
                    conversation_data_point_domain.ConversationDataPointWithDocumentFeedbackSummary(
                        **data_point.model_dump(), document_feedback_summary=None
                    )
                )
                continue

            evaluation = document_id_to_feedback_mapping.get(data_point.document_id.value, None)
            document_feedback_summary = document_feedback_domain.DocumentFeedbackSummary(
                user_id=user_id,
                document_id=data_point.document_id,
                evaluation=evaluation,
                total_good=data_point.total_good,
            )
            cdps_with_document_feedback_summary.append(
                conversation_data_point_domain.ConversationDataPointWithDocumentFeedbackSummary(
                    **data_point.model_dump(), document_feedback_summary=document_feedback_summary
                )
            )

        return cdps_with_document_feedback_summary

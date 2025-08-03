from abc import ABC, abstractmethod
import copy
import uuid

from injector import inject
from pydantic import BaseModel

from api.domain.models import (
    bot as bot_domain,
    document as document_domain,
    document_folder as document_folder_domain,
    group as group_domain,
    llm as llm_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.models.api_key.repository import IApiKeyRepository
from api.domain.models.bot.prompt_template import Id as PromptTemplateId
from api.domain.models.bot.prompt_template.prompt_template import (
    PromptTemplateForCreate,
)
from api.domain.models.bot_template import (
    BotTemplate,
    Id as BotTemplateId,
)
from api.domain.models.bot_template.repository import IBotTemplateRepository
from api.domain.models.common_document_template.repository import (
    ICommonDocumentTemplateRepository,
)
from api.domain.models.common_prompt_template.repository import (
    ICommonPromptTemplateRepository,
)
from api.domain.models.document.document import DocumentForCreate
from api.domain.models.document.repository import IDocumentRepository
from api.domain.models.document_folder import (
    IDocumentFolderRepository,
    RootDocumentFolderForCreate,
)
from api.domain.models.group.repository import IGroupRepository
from api.domain.models.llm.model import ModelFamily
from api.domain.models.search import Endpoint, EndpointsWithPriority, IndexName
from api.domain.models.text_2_image_model.model import Text2ImageModelFamily
from api.domain.services.blob_storage import IBlobStorageService
from api.domain.services.cognitive_search import ICognitiveSearchService
from api.domain.services.queue_storage.queue_storage import IQueueStorageService
from api.libs.ctx import ContextUser
from api.libs.exceptions import BadRequest, NotFound
from api.libs.feature_flag import get_feature_flag
from api.libs.logging import get_logger


class GetBotsByCurrentUserInput(BaseModel):
    tenant_id: tenant_domain.Id
    current_user: ContextUser
    statuses: list[bot_domain.Status]


class UpdateBotByUserInput(BaseModel):
    tenant_id: tenant_domain.Id
    bot_id: bot_domain.Id
    name: bot_domain.Name
    description: bot_domain.Description
    example_questions: list[bot_domain.ExampleQuestion]
    response_generator_model_family: ModelFamily
    approach: bot_domain.Approach
    response_system_prompt: bot_domain.ResponseSystemPrompt
    document_limit: bot_domain.DocumentLimit
    pdf_parser: llm_domain.PdfParser
    enable_web_browsing: bot_domain.EnableWebBrowsing
    enable_follow_up_questions: bot_domain.EnableFollowUpQuestions
    icon_color: bot_domain.IconColor
    max_conversation_turns: bot_domain.MaxConversationTurns | None
    search_method: bot_domain.SearchMethod | None


class UploadBotIconInput(BaseModel):
    file: bytes
    extension: bot_domain.IconFileExtension


class UpdateLikedBotInput(BaseModel):
    tenant_id: tenant_domain.Id
    bot_id: bot_domain.Id
    user_id: user_domain.Id
    is_liked: bot_domain.IsLiked


class IBotUseCase(ABC):
    @abstractmethod
    def get_bots_by_current_user(self, input: GetBotsByCurrentUserInput) -> list[bot_domain.BotWithGroupName]:
        pass

    @abstractmethod
    def get_bot(self, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id) -> bot_domain.Bot:
        pass

    # ユーザーAPI
    @abstractmethod
    def update_bot_by_user(
        self,
        input: UpdateBotByUserInput,
    ) -> None:
        pass

    @abstractmethod
    def find_all_bots_by_tenant_id(self, tenant_id: tenant_domain.Id) -> list[bot_domain.Bot]:
        pass

    @abstractmethod
    def upload_bot_icon(self, alias: tenant_domain.Alias, bot_id: bot_domain.Id, input: UploadBotIconInput) -> None:
        pass

    @abstractmethod
    def delete_bot_icon(self, alias: tenant_domain.Alias, bot_id: bot_domain.Id) -> None:
        pass

    @abstractmethod
    def create_bot(
        self,
        tenant_id: tenant_domain.Id,
        group_id: group_domain.Id,
        bot_for_create: bot_domain.BotForCreate,
        bot_template_id: BotTemplateId | None,
        creator_id: user_domain.Id | None,
    ) -> bot_domain.Bot:
        pass

    # 運営API
    @abstractmethod
    def update_bot(self, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id, bot: bot_domain.BotForUpdate) -> None:
        pass

    @abstractmethod
    def archive_bot(self, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id) -> None:
        pass

    @abstractmethod
    def restore_bot(self, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id) -> None:
        pass

    @abstractmethod
    def delete_bot(self, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id) -> None:
        pass

    @abstractmethod
    def find_prompt_templates_by_bot_id(
        self,
        bot_id: bot_domain.Id,
    ) -> list[bot_domain.PromptTemplate]:
        pass

    @abstractmethod
    def create_prompt_template(
        self,
        bot_id: bot_domain.Id,
        prompt_template: bot_domain.PromptTemplateForCreate,
    ) -> bot_domain.PromptTemplate:
        pass

    @abstractmethod
    def update_prompt_template(
        self,
        bot_id: bot_domain.Id,
        prompt_template: bot_domain.PromptTemplateForUpdate,
    ) -> None:
        pass

    @abstractmethod
    def delete_prompt_templates(
        self,
        bot_id: bot_domain.Id,
        bot_prompt_template_ids: list[PromptTemplateId],
    ) -> None:
        pass

    @abstractmethod
    def update_liked_bot(self, input: UpdateLikedBotInput) -> None:
        pass

    @abstractmethod
    def find_by_group_id(
        self, tenant_id: tenant_domain.Id, group_id: group_domain.Id, statuses: list[bot_domain.Status]
    ) -> list[bot_domain.Bot]:
        pass

    @abstractmethod
    def update_bot_group(self, bot_id: bot_domain.Id, group_id: group_domain.Id, tenant_id: tenant_domain.Id) -> None:
        pass


class BotUseCase(IBotUseCase):
    @inject
    def __init__(
        self,
        bot_repo: bot_domain.IBotRepository,
        cognitive_search_service: ICognitiveSearchService,
        blob_storage_service: IBlobStorageService,
        tenant_repo: tenant_domain.ITenantRepository,
        bot_template_repo: IBotTemplateRepository,
        document_folder_repo: IDocumentFolderRepository,
        common_document_template_repo: ICommonDocumentTemplateRepository,
        document_repo: IDocumentRepository,
        common_prompt_template_repo: ICommonPromptTemplateRepository,
        api_key_repo: IApiKeyRepository,
        queue_storage_service: IQueueStorageService,
        group_repo: IGroupRepository,
        user_repo: user_domain.IUserRepository,
    ) -> None:
        self.logger = get_logger()
        self.bot_repo = bot_repo
        self.cognitive_search_service = cognitive_search_service
        self.blob_storage_service = blob_storage_service
        self.tenant_repo = tenant_repo
        self.bot_template_repo = bot_template_repo
        self.common_document_template_repo = common_document_template_repo
        self.document_folder_repo = document_folder_repo
        self.document_repo = document_repo
        self.common_prompt_template_repo = common_prompt_template_repo
        self.api_key_repo = api_key_repo
        self.group_repo = group_repo
        self.queue_storage_service = queue_storage_service
        self.group_repo = group_repo
        self.user_repo = user_repo

    def _filter_bots_by_allowed_model_families(
        self,
        bots: list[bot_domain.BotWithGroupName],
        allowed_model_families: list[ModelFamily | Text2ImageModelFamily],
    ) -> list[bot_domain.BotWithGroupName]:
        filtered_bots = []
        for bot in bots:
            if bot.approach == bot_domain.Approach.TEXT_2_IMAGE:
                if (
                    bot.image_generator_model_family is not None
                    and bot.image_generator_model_family in allowed_model_families
                ):
                    filtered_bots.append(bot)
            else:
                if bot.response_generator_model_family in allowed_model_families:
                    filtered_bots.append(bot)
        return filtered_bots

    def get_bots_by_current_user(self, input: GetBotsByCurrentUserInput) -> list[bot_domain.BotWithGroupName]:
        allowed_model_families = input.current_user.tenant.allowed_model_families

        # admin users can get bots in all groups
        if input.current_user.is_admin():
            all_bots = self.bot_repo.find_with_groups_by_tenant_id(tenant_id=input.tenant_id, statuses=input.statuses)
            return self._filter_bots_by_allowed_model_families(all_bots, allowed_model_families)

        # non-admin users can get bots by their policies
        policies = self.user_repo.find_policies(input.current_user.id, input.tenant_id)
        bot_ids = [policy.bot_id for policy in policies]
        bots = self.bot_repo.find_with_groups_by_ids_and_tenant_id(bot_ids, input.tenant_id, input.statuses)
        return self._filter_bots_by_allowed_model_families(bots, allowed_model_families)

    def get_bot(self, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id) -> bot_domain.Bot:
        return self.bot_repo.find_by_id_and_tenant_id(bot_id, tenant_id)

    def _validate_pdf_parser(
        self,
        tenant: tenant_domain.Tenant,
        pdf_parser: llm_domain.PdfParser,
    ) -> None:
        if pdf_parser == llm_domain.PdfParser.DOCUMENT_INTELLIGENCE and not tenant.enable_document_intelligence.root:
            raise BadRequest("高精度表読み取り+OCR機能が有効になっていません")
        if pdf_parser == llm_domain.PdfParser.LLM_DOCUMENT_READER and not tenant.enable_llm_document_reader.root:
            raise BadRequest("LLMドキュメントリーダーが有効になっていません")

    def _validate_allowed_model_families(
        self,
        tenant: tenant_domain.Tenant,
        response_generator_model_family: ModelFamily | None,
        image_generator_model_family: Text2ImageModelFamily | None = None,
    ) -> None:
        input_models = [
            response_generator_model_family,
            image_generator_model_family,
        ]
        input_models = [model for model in input_models if model is not None]
        if any(model not in tenant.allowed_model_families for model in input_models):
            raise BadRequest("使用できないモデルが指定されています")

    def _get_available_search_service_endpoint(
        self,
        search_method: bot_domain.SearchMethod | None,
        index_name: IndexName | None,
    ) -> Endpoint:
        MAX_INDEXES_PER_ENDPOINT = 50
        if search_method not in [bot_domain.SearchMethod.URSA, bot_domain.SearchMethod.URSA_SEMANTIC]:
            raise BadRequest("不正な検索方法が指定されています")
        if index_name is None:
            raise BadRequest("インデックス名が指定されていません")
        endpoints_with_priority = self.cognitive_search_service.list_endpoints()
        available_endpoints = []
        for endpoint_with_priority in endpoints_with_priority.root:
            index_names = self.cognitive_search_service.list_index_names(endpoint=endpoint_with_priority.endpoint)
            if index_name in index_names:
                raise BadRequest("インデックス名が重複しています")
            if len(index_names) >= MAX_INDEXES_PER_ENDPOINT:
                continue
            available_endpoints.append(endpoint_with_priority)
        if len(available_endpoints) == 0:
            raise Exception("利用可能なエンドポイントがありません")
        return EndpointsWithPriority(root=available_endpoints).get_most_prioritized_endpoint()

    # ユーザーが編集可能なプロパティのみ更新する
    def update_bot_by_user(
        self,
        input: UpdateBotByUserInput,
    ) -> None:
        tenant = self.tenant_repo.find_by_id(input.tenant_id)
        self._validate_pdf_parser(tenant, input.pdf_parser)
        self._validate_allowed_model_families(tenant, input.response_generator_model_family)

        current = self.bot_repo.find_by_id_and_tenant_id(
            id=input.bot_id,
            tenant_id=input.tenant_id,
        )

        try:
            existing_bot = self.bot_repo.find_by_group_id_and_name(
                group_id=current.group_id,
                name=input.name,
            )
            if existing_bot and existing_bot.id != input.bot_id:
                raise BadRequest("アシスタントの名前が重複しています")
        except NotFound:
            pass

        bot_for_update = bot_domain.BotForUpdate.by_user(
            current=current,
            name=input.name,
            description=input.description,
            example_questions=input.example_questions,
            approach=input.approach,
            search_method=input.search_method,
            response_generator_model_family=input.response_generator_model_family,
            response_system_prompt=input.response_system_prompt,
            document_limit=input.document_limit,
            pdf_parser=input.pdf_parser,
            enable_web_browsing=input.enable_web_browsing,
            enable_follow_up_questions=input.enable_follow_up_questions,
            icon_color=input.icon_color,
            max_conversation_turns=input.max_conversation_turns,
        )

        current.update(bot_for_update)
        self.bot_repo.update(current)

    def find_all_bots_by_tenant_id(self, tenant_id: tenant_domain.Id) -> list[bot_domain.Bot]:
        return self.bot_repo.find_all_by_tenant_id(tenant_id=tenant_id)

    def upload_bot_icon(self, alias: tenant_domain.Alias, bot_id: bot_domain.Id, input: UploadBotIconInput) -> None:
        bot = self.bot_repo.find_by_id(bot_id)
        old_icon_url = bot.icon_url

        filepath = f"{alias.root}/{uuid.uuid4()}.{input.extension.value}"
        icon_url = self.blob_storage_service.upload_bot_icon(filepath, input.file)

        bot.update_icon_url(icon_url)
        self.bot_repo.update(bot)

        if old_icon_url is None:
            return
        try:
            self.blob_storage_service.delete_bot_icon(alias, old_icon_url)
        except Exception as e:
            # アイコンのアップロードは成功しているので、エラーログを出力して処理を続行
            self.logger.error(f"Failed to delete old icon: {old_icon_url}, error: {e!s}")

    def delete_bot_icon(self, alias: tenant_domain.Alias, bot_id: bot_domain.Id) -> None:
        bot = self.bot_repo.find_by_id(bot_id)
        if bot.icon_url is None:
            return
        try:
            self.blob_storage_service.delete_bot_icon(alias, bot.icon_url)
        except Exception as e:
            # アイコンの削除は失敗しているが、DBのicon_urlを削除して処理を続行
            self.logger.error(f"Failed to delete icon: {bot.icon_url}, error: {e!s}")

        bot.update_icon_url(None)
        self.bot_repo.update(bot)

    def _create_bot(
        self, tenant: tenant_domain.Tenant, group_id: group_domain.Id, bot_for_create: bot_domain.BotForCreate
    ) -> bot_domain.Bot:
        self._validate_pdf_parser(tenant, bot_for_create.pdf_parser)
        self._validate_allowed_model_families(
            tenant,
            bot_for_create.response_generator_model_family,
            bot_for_create.image_generator_model_family,
        )
        available_endpoint = None
        if bot_for_create.search_method in [bot_domain.SearchMethod.URSA, bot_domain.SearchMethod.URSA_SEMANTIC]:
            available_endpoint = self._get_available_search_service_endpoint(
                bot_for_create.search_method, bot_for_create.index_name
            )

        FEATURE_FLAG_KEY = "blob-container-renewal"
        flag = get_feature_flag(FEATURE_FLAG_KEY, tenant.id, tenant.name, default=True)
        # 同じ名前のbotが存在しないかチェック
        try:
            existing_bot = self.bot_repo.find_by_group_id_and_name(
                group_id=group_id,
                name=bot_for_create.name,
            )
            if existing_bot:
                raise BadRequest("アシスタントの名前が重複しています")
        except NotFound:
            pass

        # Blobコンテナの作成
        if not flag:
            if bot_for_create.container_name is None:
                raise BadRequest("コンテナ名が指定されていません")
            self.blob_storage_service.create_blob_container(bot_for_create.container_name)

        # chat_gpt_defaultの場合はここでDBに保存して終了
        if (
            bot_for_create.approach == bot_domain.Approach.CHAT_GPT_DEFAULT
            or bot_for_create.approach == bot_domain.Approach.CUSTOM_GPT
        ):
            return self.bot_repo.create(tenant_id=tenant.id, group_id=group_id, bot=bot_for_create)

        # Botの検索インデックスを作成
        if bot_for_create.search_method in [bot_domain.SearchMethod.URSA, bot_domain.SearchMethod.URSA_SEMANTIC]:
            if bot_for_create.index_name is None:
                raise BadRequest("インデックス名が指定されていません")
            if available_endpoint is None:
                raise Exception("利用可能なエンドポイントがありません")
            self.cognitive_search_service.create_bot_index(
                endpoint=available_endpoint,
                index_name=bot_for_create.index_name,
                search_method=bot_for_create.search_method,
            )
            bot_for_create.set_search_service_endpoint(endpoint=available_endpoint)
        return self.bot_repo.create(tenant_id=tenant.id, group_id=group_id, bot=bot_for_create)

    def _copy_template(
        self,
        tenant: tenant_domain.Tenant,
        created_bot: bot_domain.Bot,
        bot_template: BotTemplate,
        root_document_folder_id: document_folder_domain.Id | None,
        creator_id: user_domain.Id | None,
    ) -> None:
        bot = copy.deepcopy(created_bot)

        # 作成されたbot_id を元にbot_prompt_templatesテーブルを作成する
        template_prompt_templates = self.common_prompt_template_repo.find_by_bot_template_id(bot_template.id)
        for template_prompt_template in template_prompt_templates:
            prompt_template_for_create = PromptTemplateForCreate.from_template(template_prompt_template)
            self.bot_repo.create_prompt_template(bot_id=bot.id, prompt_template=prompt_template_for_create)
        # アシスタントのアイコンの内容をコピーする
        if bot_template.icon_url is not None:
            copied_icon_url = self.blob_storage_service.copy_icon_from_template(
                alias=tenant.alias,
                template_icon_url=bot_template.icon_url,
            )
            bot.update_icon_url(copied_icon_url)
            self.bot_repo.update(bot)

        # NEOLLM以外の場合はドキュメントのコピーをスキップする
        if bot.approach != bot_domain.Approach.NEOLLM or root_document_folder_id is None:
            return

        # ドキュメントの内容をコピーする
        template_documents = self.common_document_template_repo.find_by_bot_template_id(bot_template.id)
        created_document_ids_to_process = []
        created_document_ids_to_convert = []
        for template_document in template_documents:
            created_document = self.document_repo.create(
                bot_id=bot.id,
                parent_document_folder_id=root_document_folder_id,
                document=DocumentForCreate.from_template(
                    template_document,
                    creator_id=creator_id,
                ),
            )
            # blob_storageの内容をコピーする
            self.blob_storage_service.copy_blob_from_common_container_to_bot_container(
                bot_id=bot.id,
                bot_template_id=bot_template.id,
                blob_name=template_document.blob_name,
                container_name=tenant.container_name,
            )
            created_document_ids_to_process.append(created_document.id)
            if created_document.file_extension.is_convertible_to_pdf():
                created_document_ids_to_convert.append(created_document.id)

        # blob_storageから取得したblobを cognitive_searchに保存する
        if len(created_document_ids_to_process) > 0:
            self.queue_storage_service.send_messages_to_documents_process_queue(
                tenant.id, bot.id, created_document_ids_to_process
            )
        if len(created_document_ids_to_convert) > 0:
            self.queue_storage_service.send_messages_to_convert_and_upload_pdf_documents_queue(
                tenant.id, bot.id, created_document_ids_to_convert
            )

    def create_bot(
        self,
        tenant_id: tenant_domain.Id,
        group_id: group_domain.Id,
        bot_for_create: bot_domain.BotForCreate,
        bot_template_id: BotTemplateId | None,
        creator_id: user_domain.Id | None,
    ) -> bot_domain.Bot:
        tenant = self.tenant_repo.find_by_id(tenant_id)

        # グループがテナントに存在するかチェック
        self.group_repo.get_group_by_id_and_tenant_id(group_id=group_id, tenant_id=tenant_id)

        bot_template: BotTemplate | None = None
        if bot_template_id:
            bot_template = self.bot_template_repo.find_by_id(bot_template_id)
            if not bot_template.is_public.root:
                raise NotFound("テンプレートが見つかりません")

        # botを作成する
        created_bot = self._create_bot(tenant, group_id, bot_for_create)

        # botに対する rootフォルダを作成する
        created_root_document_folder = None
        if created_bot.approach in [
            bot_domain.Approach.NEOLLM,
            bot_domain.Approach.CUSTOM_GPT,
            bot_domain.Approach.URSA,
        ]:
            try:
                root_document_folder = self.document_folder_repo.find_root_document_folder_by_bot_id(
                    bot_id=created_bot.id,
                )
                if root_document_folder is not None:
                    raise Exception("rootフォルダが既に存在しています")
            except NotFound:
                pass

            created_root_document_folder = self.document_folder_repo.create_root_document_folder(
                bot_id=created_bot.id,
                root_document_folder_for_create=RootDocumentFolderForCreate(),
            )

        # テンプレートを使用している場合ドキュメント、プロンプトのテンプレートも作成されたbotに対して登録する
        if bot_template:
            self._copy_template(
                tenant,
                created_bot,
                bot_template,
                created_root_document_folder.id if created_root_document_folder is not None else None,
                creator_id,
            )

        return created_bot

    # 運営が編集可能なプロパティのみ更新する
    def update_bot(self, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id, bot: bot_domain.BotForUpdate) -> None:
        tenant = self.tenant_repo.find_by_id(tenant_id)
        self._validate_pdf_parser(tenant, bot.pdf_parser)
        self._validate_allowed_model_families(
            tenant,
            bot.response_generator_model_family,
            bot.image_generator_model_family,
        )

        current = self.bot_repo.find_by_id_and_tenant_id(bot_id, tenant_id)

        try:
            existing_bot = self.bot_repo.find_by_group_id_and_name(
                group_id=current.group_id,
                name=bot.name,
            )
            if existing_bot and existing_bot.id != bot_id:
                raise BadRequest("アシスタントの名前が重複しています")
        except NotFound:
            pass

        current.update(bot)

        self.bot_repo.update(current)

    def archive_bot(self, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id) -> None:
        bot = self.bot_repo.find_by_id_and_tenant_id(bot_id, tenant_id)
        bot.archive()
        self.bot_repo.update(bot)

    def restore_bot(self, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id) -> None:
        bot = self.bot_repo.find_by_id_and_tenant_id(bot_id, tenant_id)
        bot.restore()
        self.bot_repo.update(bot)

    def delete_bot(self, tenant_id: tenant_domain.Id, bot_id: bot_domain.Id) -> None:
        # TODO: blob-container-renewal が終わったらリファクタ
        tenant = self.tenant_repo.find_by_id(tenant_id)
        bot = self.bot_repo.find_by_id_and_tenant_id(bot_id, tenant_id)
        documents = self.document_repo.find_by_bot_id(bot_id)

        if bot.status == bot_domain.Status.DELETING:
            raise BadRequest("削除中のアシスタントは削除できません")
        if any(document.status == document_domain.Status.DELETING for document in documents):
            raise BadRequest("削除中のドキュメントが含まれています")
        if not all(
            document.status == document_domain.Status.COMPLETED or document.status == document_domain.Status.FAILED
            for document in documents
        ):
            raise BadRequest("処理中のドキュメントが含まれています")
        # status を DELETING に変更
        bot.delete()
        self.bot_repo.update(bot)

        for document in documents:
            document.update_status_to_deleting()
        self.document_repo.bulk_update(documents)
        # queue に削除メッセージを送信
        self.queue_storage_service.send_message_to_delete_bot_queue(tenant.id, bot.id)

    def find_prompt_templates_by_bot_id(
        self,
        bot_id: bot_domain.Id,
    ) -> list[bot_domain.PromptTemplate]:
        return self.bot_repo.find_prompt_templates_by_bot_id(bot_id=bot_id)

    def create_prompt_template(
        self,
        bot_id: bot_domain.Id,
        prompt_template: bot_domain.PromptTemplateForCreate,
    ) -> bot_domain.PromptTemplate:
        return self.bot_repo.create_prompt_template(bot_id=bot_id, prompt_template=prompt_template)

    def update_prompt_template(
        self,
        bot_id: bot_domain.Id,
        prompt_template: bot_domain.PromptTemplateForUpdate,
    ) -> None:
        current = self.bot_repo.find_prompt_template_by_id_and_bot_id(
            bot_id=bot_id,
            bot_prompt_template_id=prompt_template.id,
        )
        current.update(prompt_template)
        self.bot_repo.update_prompt_template(bot_id=bot_id, prompt_template=current)

    def delete_prompt_templates(
        self,
        bot_id: bot_domain.Id,
        bot_prompt_template_ids: list[PromptTemplateId],
    ) -> None:
        self.bot_repo.delete_prompt_templates(bot_id=bot_id, bot_prompt_template_ids=bot_prompt_template_ids)

    def update_liked_bot(self, input: UpdateLikedBotInput) -> None:
        bot = self.bot_repo.find_by_id_and_tenant_id(id=input.bot_id, tenant_id=input.tenant_id)
        if bot_domain.Approach.is_basic_ai(bot.approach):
            raise BadRequest("基盤モデルはお気に入り登録できません")

        exist_fav_bot_ids = self.bot_repo.find_liked_bot_ids_by_user_id(user_id=input.user_id)

        if input.is_liked.root:
            if input.bot_id in exist_fav_bot_ids:
                return
            self.bot_repo.add_liked_bot(tenant_id=input.tenant_id, bot_id=input.bot_id, user_id=input.user_id)
        else:
            if input.bot_id not in exist_fav_bot_ids:
                return
            self.bot_repo.remove_liked_bot(bot_id=input.bot_id, user_id=input.user_id)

    def find_by_group_id(
        self, tenant_id: tenant_domain.Id, group_id: group_domain.Id, statuses: list[bot_domain.Status]
    ) -> list[bot_domain.Bot]:
        return self.bot_repo.find_by_group_id(tenant_id=tenant_id, group_id=group_id, statuses=statuses)

    def update_bot_group(self, bot_id: bot_domain.Id, group_id: group_domain.Id, tenant_id: tenant_domain.Id) -> None:
        group = self.group_repo.get_group_by_id_and_tenant_id(group_id=group_id, tenant_id=tenant_id)
        bot = self.bot_repo.find_by_id_and_tenant_id(id=bot_id, tenant_id=tenant_id)

        try:
            existing_bot = self.bot_repo.find_by_group_id_and_name(
                group_id=group_id,
                name=bot.name,
            )
            if existing_bot.id != bot.id:
                raise BadRequest("変更後のグループに同じ名前のアシスタントが存在します")
        except NotFound:
            pass

        return self.bot_repo.update_bot_group(bot_id=bot.id, group_id=group.id)

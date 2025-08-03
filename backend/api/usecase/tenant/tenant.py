from abc import ABC, abstractmethod
import asyncio

from injector import inject
from pydantic import BaseModel, ConfigDict

from api.domain.models import (
    bot as bot_domain,
    group as group_domain,
    llm as llm_domain,
    metering as metering_domain,
    prompt_template as pt_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.models.llm.model import ModelFamily
from api.domain.models.search import Endpoint, EndpointsWithPriority, IndexName, StorageUsage
from api.domain.models.tenant import (
    external_data_connection as external_data_connection_domain,
    guideline as guideline_domain,
)
from api.domain.models.tenant.statistics import UserCount
from api.domain.models.text_2_image_model.model import Text2ImageModelFamily
from api.domain.services.blob_storage import IBlobStorageService
from api.domain.services.box.box import IBoxService
from api.domain.services.cognitive_search import ICognitiveSearchService
from api.domain.services.queue_storage.queue_storage import IQueueStorageService
from api.infrastructures.auth0.auth0 import IAuth0Service
from api.infrastructures.msgraph.msgraph import IMsgraphService
from api.libs.exceptions import BadRequest, NotFound
from api.libs.feature_flag import get_feature_flag_with_anonymous_context


class UpdateTenantLogoInput(BaseModel):
    tenant_id: tenant_domain.Id
    file_name: str
    logo_file: bytes


class UpdateTenantBasicAiInput(BaseModel):
    model_config = ConfigDict(protected_namespaces=("model_family_",))

    tenant: tenant_domain.Tenant
    model_family: ModelFamily | Text2ImageModelFamily
    enabled: bool


class UpdateTenantAllowedModelFamilyInput(BaseModel):
    model_config = ConfigDict(protected_namespaces=("model_family_",))

    tenant_id: tenant_domain.Id
    model_family: ModelFamily | Text2ImageModelFamily
    is_allowed: bool


class CreateTenantOutput(BaseModel):
    tenant: tenant_domain.Tenant
    admin: user_domain.User
    group_id: group_domain.Id


class GetGuidelineOutput(BaseModel):
    id: guideline_domain.Id
    filename: guideline_domain.Filename
    signed_url: str
    created_at: guideline_domain.CreatedAt


class ITenantUseCase(ABC):
    @abstractmethod
    def create_tenant(
        self,
        tenant: tenant_domain.TenantForCreate,
        user: user_domain.UserForCreate,
    ) -> CreateTenantOutput:
        pass

    @abstractmethod
    def get_tenants(self) -> list[tenant_domain.Tenant]:
        pass

    @abstractmethod
    def get_tenant_by_id(self, tenant_id: tenant_domain.Id) -> tenant_domain.Tenant:
        pass

    @abstractmethod
    def get_tenant_storage_usage(
        self,
        tenant_id: tenant_domain.Id,
    ) -> StorageUsage:
        pass

    @abstractmethod
    def update_tenant(self, tenant_id: tenant_domain.Id, tenant_for_update: tenant_domain.TenantForUpdate) -> None:
        pass

    @abstractmethod
    def delete_tenant(self, tenant_id: tenant_domain.Id) -> None:
        pass

    @abstractmethod
    def update_tenant_masked(
        self, tenant_id: tenant_domain.Id, is_sensitive_masked: tenant_domain.IsSensitiveMasked
    ) -> None:
        pass

    @abstractmethod
    def get_tenant_user_count(
        self,
        tenant_id: tenant_domain.Id,
    ) -> UserCount:
        pass

    @abstractmethod
    def upload_logo(self, input: UpdateTenantLogoInput) -> None:
        pass

    @abstractmethod
    def update_tenant_basic_ai(self, input: UpdateTenantBasicAiInput) -> None:
        pass

    @abstractmethod
    def update_tenant_basic_ai_web_browsing(
        self, tenant_id: tenant_domain.Id, enable_basic_ai_web_browsing: tenant_domain.EnableBasicAiWebBrowsing
    ) -> None:
        pass

    @abstractmethod
    def update_tenant_basic_ai_pdf_parser(
        self, tenant_id: tenant_domain.Id, basic_ai_pdf_parser: llm_domain.BasicAiPdfParser
    ) -> None:
        pass

    @abstractmethod
    def update_tenant_max_attachment_token(
        self, tenant_id: tenant_domain.Id, max_attachment_token: tenant_domain.MaxAttachmentToken
    ) -> None:
        pass

    @abstractmethod
    def update_tenant_allowed_model_family(self, input: UpdateTenantAllowedModelFamilyInput) -> None:
        pass

    @abstractmethod
    def update_tenant_basic_ai_max_conversation_turns(
        self,
        tenant_id: tenant_domain.Id,
        basic_ai_max_conversation_turns: tenant_domain.BasicAiMaxConversationTurns | None,
    ) -> None:
        pass

    @abstractmethod
    def get_guidelines_by_tenant_id(
        self,
        tenant_id: tenant_domain.Id,
    ) -> list[guideline_domain.Guideline]:
        pass

    @abstractmethod
    def upload_guideline(
        self, tenant_id: tenant_domain.Id, filename: guideline_domain.Filename, file_content: bytes
    ) -> None:
        pass

    @abstractmethod
    def get_guideline_by_id_and_tenant_id(
        self,
        id: guideline_domain.Id,
        tenant_id: tenant_domain.Id,
    ) -> GetGuidelineOutput:
        pass

    @abstractmethod
    def delete_guideline(self, id: guideline_domain.Id, tenant_id: tenant_domain.Id) -> None:
        pass

    @abstractmethod
    def get_external_data_connections(
        self, tenant_id: tenant_domain.Id
    ) -> list[external_data_connection_domain.ExternalDataConnection]:
        pass

    @abstractmethod
    def create_external_data_connection(
        self, external_data_connection: external_data_connection_domain.ExternalDataConnectionForCreate
    ) -> None:
        pass

    @abstractmethod
    def delete_external_data_connection(
        self, tenant_id: tenant_domain.Id, external_data_connection_id: external_data_connection_domain.Id
    ) -> None:
        pass


class TenantUseCase(ITenantUseCase):
    @inject
    def __init__(
        self,
        tenant_repo: tenant_domain.ITenantRepository,
        metering_repo: metering_domain.IMeteringRepository,
        prompt_template_repo: pt_domain.IPromptTemplateRepository,
        group_repo: group_domain.IGroupRepository,
        user_repo: user_domain.IUserRepository,
        bot_repo: bot_domain.IBotRepository,
        auth0_service: IAuth0Service,
        cognitive_search_service: ICognitiveSearchService,
        blob_storage_service: IBlobStorageService,
        queue_storage_service: IQueueStorageService,
        msgraph_service: IMsgraphService,
        box_service: IBoxService,
    ) -> None:
        self.tenant_repo = tenant_repo
        self.metering_repo = metering_repo
        self.user_repo = user_repo
        self.bot_repo = bot_repo
        self.prompt_template_repo = prompt_template_repo
        self.group_repo = group_repo
        self.auth0_service = auth0_service
        self.cognitive_search_service = cognitive_search_service
        self.blob_storage_service = blob_storage_service
        self.queue_storage_service = queue_storage_service
        self.msgraph_service = msgraph_service
        self.box_service = box_service

    def _get_available_search_service_endpoint(
        self,
        index_name: IndexName,
    ) -> Endpoint:
        MAX_INDEXES_PER_ENDPOINT = 50
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

    def create_tenant(
        self,
        tenant_for_create: tenant_domain.TenantForCreate,
        admin: user_domain.UserForCreate,
    ) -> CreateTenantOutput:
        # aliasが重複していないかチェック
        try:
            if tenant_for_create.alias:
                self.tenant_repo.find_by_alias(tenant_for_create.alias)
        except NotFound:
            pass

        # index_nameが重複していないかチェック
        search_service_endpoint = self._get_available_search_service_endpoint(tenant_for_create.index_name)
        tenant_for_create.set_search_service_endpoint(endpoint=search_service_endpoint)

        # adminのemailが重複していないかチェック
        users = self.auth0_service.find_by_emails([admin.email])
        if len(users) > 0:
            raise BadRequest("このメールアドレスは既に使用されています。")

        try:
            user_found_by_email = self.user_repo.find_by_email(admin.email)
            if user_found_by_email is not None:
                raise BadRequest("このメールアドレスは既に使用されています。")
        except NotFound:
            pass

        # tenant作成
        tenant = self.tenant_repo.create(tenant_for_create)

        # auth0にuserを作成
        auth0_user_id = self.auth0_service.create_user(admin.email)

        # DBにadmin_userを作成&テナントに紐付け
        admin_user_id = self.user_repo.create(
            tenant_id=tenant.id,
            user=admin,
            auth0_id=auth0_user_id,
        )

        group = self.group_repo.create_group(
            tenant_id=tenant.id,
            name=group_domain.Name(value=f"{tenant.name.value} All"),
            is_general=group_domain.IsGeneral(root=True),
        )

        # Allにadminを追加
        self.group_repo.add_users_to_group(
            tenant_id=tenant.id,
            group_id=group.id,
            user_ids=[admin_user_id],
            group_role=group_domain.GroupRole.GROUP_ADMIN,
        )

        BLOB_CONTAINER_RENEWAL_FLAG_KEY = "blob-container-renewal"
        blob_container_renewal_flag = get_feature_flag_with_anonymous_context(
            BLOB_CONTAINER_RENEWAL_FLAG_KEY, default=True
        )

        DALL_E_3_FLAG_KEY = "tmp-dall-e-3"
        dall_e_3_flag = get_feature_flag_with_anonymous_context(DALL_E_3_FLAG_KEY)
        bots_for_create: list[bot_domain.BotForCreate] = []

        # 許容されているモデルファミリーの基本AIを作成
        for model_family in tenant.allowed_model_families:
            if isinstance(model_family, ModelFamily):
                bots_for_create.append(
                    bot_domain.BasicAiForCreate(
                        tenant=tenant,
                        model_family=model_family,
                    )
                )
            elif isinstance(model_family, Text2ImageModelFamily) and dall_e_3_flag:
                bots_for_create.append(
                    bot_domain.Text2ImageBotForCreate(
                        tenant=tenant,
                        model_family=model_family,
                    )
                )

        for bot_for_create in bots_for_create:
            if not blob_container_renewal_flag and bot_for_create.approach == bot_domain.Approach.CHAT_GPT_DEFAULT:
                if bot_for_create.container_name is None:
                    raise BadRequest("コンテナ名が指定されていません。")
                self.blob_storage_service.create_blob_container(bot_for_create.container_name)
            self.bot_repo.create(tenant_id=tenant.id, group_id=group.id, bot=bot_for_create)

        default_prompt_templates = pt_domain.DefaultPromptTemplates()
        self.prompt_template_repo.bulk_create(
            tenant_id=tenant.id,
            prompt_templates=default_prompt_templates.prompt_templates,
        )

        # cognitive searchのindexを作成
        self.cognitive_search_service.create_tenant_index(
            endpoint=search_service_endpoint,
            index_name=tenant.index_name,
        )

        # blob storageのcontainerを作成
        if blob_container_renewal_flag:
            self.blob_storage_service.create_blob_container(tenant.container_name)

        return CreateTenantOutput(
            tenant=tenant,
            admin=user_domain.User(
                id=admin_user_id,
                name=admin.name,
                email=admin.email,
                roles=admin.roles,
                policies=[],
            ),
            group_id=group.id,
        )

    def get_tenants(self) -> list[tenant_domain.Tenant]:
        return self.tenant_repo.find_all()

    def get_tenant_by_id(
        self,
        tenant_id: tenant_domain.Id,
    ) -> tenant_domain.Tenant:
        return self.tenant_repo.find_by_id(tenant_id)

    def get_tenant_storage_usage(
        self,
        tenant_id: tenant_domain.Id,
    ) -> StorageUsage:
        tenant = self.tenant_repo.find_by_id(tenant_id)
        return self.cognitive_search_service.get_index_storage_usage(
            endpoint=tenant.search_service_endpoint,
            index_name=tenant.index_name,
        )

    def update_tenant(self, tenant_id: tenant_domain.Id, tenant_for_update: tenant_domain.TenantForUpdate) -> None:
        current = self.tenant_repo.find_by_id(tenant_id)

        current.update(tenant_for_update)

        return self.tenant_repo.update(current)

    def delete_tenant(self, tenant_id: tenant_domain.Id) -> None:
        FEATURE_FLAG_KEY = "blob-container-renewal"
        flag = get_feature_flag_with_anonymous_context(FEATURE_FLAG_KEY, default=True)

        # neoAIテナントは消せないように
        if tenant_id == 1:
            raise BadRequest("このテナントは削除できません。")

        bots = self.bot_repo.find_all_by_tenant_id(tenant_id)
        if len(bots) > 0:
            raise BadRequest("このテナントにはボットが紐づいています。ボットを削除してから再度お試しください。")

        tenant = self.tenant_repo.find_by_id(tenant_id)
        users = self.user_repo.find_by_tenant_id(tenant_id)

        # auth0からユーザー削除
        self.auth0_service.delete_users([user.email for user in users])

        # 物理削除 job 実行前に論理削除
        # bot 関連のデータはすでに論理削除済み
        self.group_repo.delete_by_tenant_id(tenant_id)
        self.user_repo.delete_by_tenant_id(tenant_id)
        self.prompt_template_repo.delete_by_tenant_id(tenant_id)
        self.metering_repo.delete_by_tenant_id(tenant_id)
        self.tenant_repo.delete(tenant_id)

        self.cognitive_search_service.delete_index(
            endpoint=tenant.search_service_endpoint,
            index_name=tenant.index_name,
        )
        if flag:
            if tenant.container_name is None:
                raise BadRequest("このテナントにはコンテナが紐づいていません。")
            self.blob_storage_service.delete_blob_container(tenant.container_name)

        self.queue_storage_service.send_message_to_delete_tenant_queue(tenant_id)

    def update_tenant_masked(
        self, tenant_id: tenant_domain.Id, is_sensitive_masked: tenant_domain.IsSensitiveMasked
    ) -> None:
        self.tenant_repo.update_masked(tenant_id, is_sensitive_masked)

    def get_tenant_user_count(
        self,
        tenant_id: tenant_domain.Id,
    ) -> UserCount:
        return self.tenant_repo.get_user_count(tenant_id)

    def upload_logo(self, input: UpdateTenantLogoInput) -> None:
        tenant = self.tenant_repo.find_by_id(input.tenant_id)

        logo_url = self.blob_storage_service.upload_image_to_common_container(input.file_name, input.logo_file)

        tenant.update_logo_url(logo_url)

        return self.tenant_repo.update(tenant)

    def update_tenant_basic_ai(self, input: UpdateTenantBasicAiInput) -> None:
        general_group = self.group_repo.find_general_group_by_tenant_id(input.tenant.id)

        try:
            if isinstance(input.model_family, ModelFamily):
                bot = self.bot_repo.find_basic_ai_by_response_generator_model_family(
                    tenant_id=input.tenant.id,
                    group_id=general_group.id,
                    model_family=input.model_family,
                    statuses=[
                        bot_domain.Status.ACTIVE,
                        bot_domain.Status.ARCHIVED,
                        bot_domain.Status.BASIC_AI_DELETED,
                    ],
                )
            elif isinstance(input.model_family, Text2ImageModelFamily):
                bot = self.bot_repo.find_basic_ai_by_image_generator_model_family(
                    tenant_id=input.tenant.id,
                    group_id=general_group.id,
                    model_family=input.model_family,
                    statuses=[
                        bot_domain.Status.ACTIVE,
                        bot_domain.Status.ARCHIVED,
                        bot_domain.Status.BASIC_AI_DELETED,
                    ],
                )
        except NotFound:
            bot = None

        if bot is None:
            if input.enabled:
                bot_for_create = (
                    bot_domain.BasicAiForCreate(tenant=input.tenant, model_family=input.model_family)
                    if isinstance(input.model_family, ModelFamily)
                    else bot_domain.Text2ImageBotForCreate(tenant=input.tenant, model_family=input.model_family)
                )
                self.bot_repo.create(tenant_id=input.tenant.id, group_id=general_group.id, bot=bot_for_create)
            return

        if not input.enabled:
            bot.delete_basic_ai()
            self.bot_repo.update(bot)
        elif bot.status == bot_domain.Status.BASIC_AI_DELETED:
            bot.restore()
            self.bot_repo.update(bot)

    def update_tenant_basic_ai_web_browsing(
        self, tenant_id: tenant_domain.Id, enable_basic_ai_web_browsing: tenant_domain.EnableBasicAiWebBrowsing
    ) -> None:
        tenant = self.tenant_repo.find_by_id(tenant_id)
        tenant.update_basic_ai_web_browsing(enable_basic_ai_web_browsing)
        return self.tenant_repo.update(tenant)

    def update_tenant_basic_ai_pdf_parser(
        self, tenant_id: tenant_domain.Id, basic_ai_pdf_parser: llm_domain.BasicAiPdfParser
    ) -> None:
        tenant = self.tenant_repo.find_by_id(tenant_id)
        tenant.update_basic_ai_pdf_parser(basic_ai_pdf_parser)
        return self.tenant_repo.update(tenant)

    def update_tenant_max_attachment_token(
        self, tenant_id: tenant_domain.Id, max_attachment_token: tenant_domain.MaxAttachmentToken
    ) -> None:
        tenant = self.tenant_repo.find_by_id(tenant_id)
        tenant.update_max_attachment_token(max_attachment_token)
        return self.tenant_repo.update(tenant)

    def update_tenant_allowed_model_family(self, input: UpdateTenantAllowedModelFamilyInput) -> None:
        tenant = self.tenant_repo.find_by_id(input.tenant_id)
        bots = self.bot_repo.find_by_tenant_id(
            tenant.id, statuses=[bot_domain.Status.ACTIVE, bot_domain.Status.ARCHIVED]
        )
        # model_familyとtext2image_model_familyを重複をなくして一つのsetにする
        tenant_bot_model_family_set: set[ModelFamily | Text2ImageModelFamily] = {
            model
            for bot in bots
            for model in (bot.response_generator_model_family, bot.image_generator_model_family)
            if model is not None
        }
        tenant.update_allowed_model_family(input.model_family, input.is_allowed, list(tenant_bot_model_family_set))
        return self.tenant_repo.update(tenant)

    def update_tenant_basic_ai_max_conversation_turns(
        self,
        tenant_id: tenant_domain.Id,
        basic_ai_max_conversation_turns: tenant_domain.BasicAiMaxConversationTurns | None,
    ) -> None:
        tenant = self.tenant_repo.find_by_id(tenant_id)
        tenant.update_basic_ai_max_conversation_turns(basic_ai_max_conversation_turns)
        return self.tenant_repo.update(tenant)

    def get_guidelines_by_tenant_id(
        self,
        tenant_id: tenant_domain.Id,
    ) -> list[guideline_domain.Guideline]:
        return self.tenant_repo.get_guidelines_by_tenant_id(tenant_id)

    def upload_guideline(
        self, tenant_id: tenant_domain.Id, filename: guideline_domain.Filename, file_content: bytes
    ) -> None:
        tenant = self.tenant_repo.find_by_id(tenant_id)

        try:
            existing_guideline = self.tenant_repo.get_guideline_by_tenant_id_and_filename(tenant_id, filename)
            if existing_guideline is not None:
                raise BadRequest("このファイル名は既に使用されています。")
        except NotFound:
            pass

        self.tenant_repo.create_guideline(guideline_domain.GuidelineForCreate(tenant_id=tenant_id, filename=filename))

        self.blob_storage_service.upload_guideline(
            container_name=tenant.container_name, blob_path=f"guidelines/{filename.value}", file_content=file_content
        )

    def get_guideline_by_id_and_tenant_id(
        self,
        id: guideline_domain.Id,
        tenant_id: tenant_domain.Id,
    ) -> GetGuidelineOutput:
        tenant = self.tenant_repo.find_by_id(tenant_id)

        guideline = self.tenant_repo.get_guideline_by_id_and_tenant_id(id, tenant_id)
        signed_url = self.blob_storage_service.create_guideline_sas_url(
            container_name=tenant.container_name,
            blob_path=f"guidelines/{guideline.filename.value}",
        )

        return GetGuidelineOutput(
            id=guideline.id, filename=guideline.filename, signed_url=signed_url, created_at=guideline.created_at
        )

    def delete_guideline(self, id: guideline_domain.Id, tenant_id: tenant_domain.Id) -> None:
        tenant = self.tenant_repo.find_by_id(tenant_id)

        guideline = self.tenant_repo.get_guideline_by_id_and_tenant_id(id, tenant_id)

        self.blob_storage_service.delete_guideline(
            container_name=tenant.container_name, blob_path=f"guidelines/{guideline.filename.value}"
        )

        self.tenant_repo.delete_guideline(id, tenant_id)

    def get_external_data_connections(
        self, tenant_id: tenant_domain.Id
    ) -> list[external_data_connection_domain.ExternalDataConnection]:
        return self.tenant_repo.get_external_data_connections(tenant_id)

    def create_external_data_connection(
        self, external_data_connection: external_data_connection_domain.ExternalDataConnectionForCreate
    ) -> None:
        tenant = self.tenant_repo.find_by_id(external_data_connection.tenant_id)

        if not tenant.enable_external_data_integrations.root:
            raise BadRequest("外部データ連携が無効です。")

        match external_data_connection.external_data_connection_type:
            case external_data_connection_domain.ExternalDataConnectionType.SHAREPOINT:
                is_authorized = asyncio.run(
                    self.msgraph_service.is_authorized_client(
                        external_data_connection.decrypted_credentials.to_sharepoint_credentials()
                    )
                )
                if not is_authorized:
                    raise BadRequest("権限がありません。Files.Read.All以上の権限が必要です。")
            case external_data_connection_domain.ExternalDataConnectionType.BOX:
                is_authorized = self.box_service.is_authorized_client(
                    external_data_connection.decrypted_credentials.to_box_credentials()
                )
                if not is_authorized:
                    raise BadRequest("権限がありません。Box管理者によってアプリが承認されているか確認してください。")
            case _:
                raise BadRequest("未対応の外部データ連携です。")

        self.tenant_repo.create_external_data_connection(external_data_connection)

    def delete_external_data_connection(
        self, tenant_id: tenant_domain.Id, external_data_connection_id: external_data_connection_domain.Id
    ) -> None:
        self.tenant_repo.hard_delete_external_data_connection(tenant_id, external_data_connection_id)

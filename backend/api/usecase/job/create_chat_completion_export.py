from abc import ABC, abstractmethod

from injector import inject

from api.domain.models import (
    api_key as api_key_domain,
    bot as bot_domain,
    chat_completion as chat_completion_domain,
    chat_completion_export as chat_completion_export_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.services.blob_storage import IBlobStorageService
from api.libs.csv import convert_dict_list_to_csv_bytes
from api.libs.exceptions import BadRequest, NotFound
from api.usecase.chat_completion.types import (
    BotWithApiKeys,
    ChatCompletionWithBotAndApiKey,
)


class ICreateChatCompletionExportUseCase(ABC):
    @abstractmethod
    def create_chat_completion_export(
        self, tenant_id: tenant_domain.Id, chat_completion_id: chat_completion_export_domain.Id
    ):
        pass


class CreateChatCompletionExportUseCase(ICreateChatCompletionExportUseCase):
    @inject
    def __init__(
        self,
        bot_repo: bot_domain.IBotRepository,
        chat_completion_repo: chat_completion_domain.IChatCompletionRepository,
        chat_completion_export_repo: chat_completion_export_domain.IChatCompletionExportRepository,
        tenant_repo: tenant_domain.ITenantRepository,
        api_key_repo: api_key_domain.IApiKeyRepository,
        user_repo: user_domain.IUserRepository,
        blob_storage_service: IBlobStorageService,
    ):
        self.bot_repo = bot_repo
        self.chat_completion_repo = chat_completion_repo
        self.chat_completion_export_repo = chat_completion_export_repo
        self.tenant_repo = tenant_repo
        self.api_key_repo = api_key_repo
        self.user_repo = user_repo
        self.blob_storage_service = blob_storage_service

    def create_chat_completion_export(
        self, tenant_id: tenant_domain.Id, chat_completion_id: chat_completion_export_domain.Id
    ):
        chat_completion_export = self.chat_completion_export_repo.find_by_id(
            tenant_id=tenant_id, id=chat_completion_id
        )

        tenant = self.tenant_repo.find_by_id(tenant_id)

        bot_with_api_keys_list, api_key_ids = self._get_bot_with_api_keys_list(
            bot_id=chat_completion_export.target_bot_id,
            api_key_id=chat_completion_export.target_api_key_id,
            tenant_id=tenant_id,
        )

        chat_completions = self.chat_completion_repo.find_by_api_key_ids_and_date(
            api_key_ids=api_key_ids,
            start_date_time=chat_completion_export.start_date_time.root,
            end_date_time=chat_completion_export.end_date_time.root,
        )

        data = [
            ChatCompletionWithBotAndApiKey.from_chat_completion_and_bot_with_api_keys_list(
                chat_completion, bot_with_api_keys_list
            )
            for chat_completion in chat_completions
        ]

        dicts = [item.to_dict() for item in data]
        csv_bytes = convert_dict_list_to_csv_bytes(data=dicts)

        # csvをblobにアップロード
        self.blob_storage_service.upload_chat_completion_export_csv(
            container_name=tenant.container_name, blob_path=chat_completion_export.blob_path, csv=csv_bytes
        )

        # conversation_exportを更新
        chat_completion_export.update_status_to_active()
        self.chat_completion_export_repo.update(chat_completion_export)

    def _get_bot_with_api_keys_list(
        self, bot_id: bot_domain.Id | None, api_key_id: api_key_domain.Id | None, tenant_id: tenant_domain.Id
    ) -> tuple[list[BotWithApiKeys], list[api_key_domain.Id]]:
        # テナントに紐づく全ボットIDとAPIキーIDを取得
        tenant_bots = self.bot_repo.find_all_by_tenant_id(tenant_id=tenant_id, include_deleted=True)
        tenant_bot_ids = [bot.id for bot in tenant_bots]

        if bot_id and bot_id not in tenant_bot_ids:
            raise NotFound("アシスタントが見つかりませんでした")

        if bot_id is None and api_key_id is None:
            api_keys = self.api_key_repo.find_by_bot_ids(tenant_bot_ids, include_deleted=True)
            bot_with_api_keys_list = [BotWithApiKeys(bot=bot, api_keys=api_keys) for bot in tenant_bots]
            api_key_ids = [api_key.id for api_key in api_keys]
            return bot_with_api_keys_list, api_key_ids

        if bot_id is not None:
            bot = self.bot_repo.find_by_id(bot_id, include_deleted=True)
            api_keys = (
                [self.api_key_repo.find_by_id_and_bot_id(api_key_id, bot_id, include_deleted=True)]
                if api_key_id is not None
                else self.api_key_repo.find_by_bot_ids([bot_id], include_deleted=True)
            )
            bot_with_api_keys_list = [BotWithApiKeys(bot=bot, api_keys=api_keys)]
            api_key_ids = [api_key.id for api_key in api_keys]
            return bot_with_api_keys_list, api_key_ids

        raise BadRequest("不正なリクエストです")

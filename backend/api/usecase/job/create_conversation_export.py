from abc import ABC, abstractmethod

from injector import inject

from api.domain.models import (
    bot as bot_domain,
    conversation as conversation_domain,
    conversation_export as conversation_export_domain,
    document_folder as document_folder_domain,
    tenant as tenant_domain,
    user as user_domain,
)
from api.domain.services.blob_storage import IBlobStorageService
from api.libs.csv import convert_dict_list_to_csv_bytes


class ICreateConversationExportUseCase(ABC):
    @abstractmethod
    def create_conversation_export(
        self, tenant_id: tenant_domain.Id, conversation_export_id: conversation_export_domain.Id
    ):
        pass


class CreateConversationExportUseCase(ICreateConversationExportUseCase):
    @inject
    def __init__(
        self,
        bot_repo: bot_domain.IBotRepository,
        conversation_repo: conversation_domain.IConversationRepository,
        conversation_export_repo: conversation_export_domain.IConversationExportRepository,
        tenant_repo: tenant_domain.ITenantRepository,
        user_repo: user_domain.IUserRepository,
        blob_storage_service: IBlobStorageService,
        document_folder_repo: document_folder_domain.IDocumentFolderRepository,
    ):
        self.bot_repo = bot_repo
        self.conversation_export_repo = conversation_export_repo
        self.conversation_repo = conversation_repo
        self.tenant_repo = tenant_repo
        self.user_repo = user_repo
        self.blob_storage_service = blob_storage_service
        self.document_folder_repo = document_folder_repo

    def create_conversation_export(
        self, tenant_id: tenant_domain.Id, conversation_export_id: conversation_export_domain.Id
    ):
        conversation_export = self.conversation_export_repo.find_by_id(tenant_id=tenant_id, id=conversation_export_id)

        tenant = self.tenant_repo.find_by_id(tenant_id)

        if conversation_export.target_user_id is not None:
            # conversation_export.target_user_id is validated to belong to the tenant before being inserted into the db
            user_ids = [conversation_export.target_user_id]
        else:
            user_ids = [
                user.id for user in self.user_repo.find_by_tenant_id(tenant_id=tenant_id, include_deleted=True)
            ]

        if conversation_export.target_bot_id is not None:
            # conversation_export.target_bot_id is validated to belong to the tenant before being inserted into the db
            bot_ids = [conversation_export.target_bot_id]
        else:
            bot_ids = [
                bot.id for bot in self.bot_repo.find_all_by_tenant_id(tenant_id=tenant_id, include_deleted=True)
            ]

        conversation_turns = self.conversation_repo.find_conversation_turns_by_user_ids_bot_ids_and_date_v2(
            user_ids=user_ids,
            bot_ids=bot_ids,
            start_date_time=conversation_export.start_date_time.root,
            end_date_time=conversation_export.end_date_time.root,
        )

        dicts = [conversation_turn.to_dict() for conversation_turn in conversation_turns]

        # CSVを作成
        csv_bytes = convert_dict_list_to_csv_bytes(data=dicts, column_order=self._initialize_column_order(dicts))

        # csvをblobにアップロード
        self.blob_storage_service.upload_conversation_export_csv(
            container_name=tenant.container_name, blob_path=conversation_export.blob_path, csv=csv_bytes
        )

        # conversation_exportを更新
        conversation_export.update_status_to_active()
        self.conversation_export_repo.update(conversation_export)

    def _initialize_column_order(self, data: list[dict[str, str]]) -> list:
        # Base column order
        column_order = [
            "ユーザー",
            "基盤モデル/アシスタント",
            "入力",
            "出力",
            "会話日時",
            "回答生成モデル",
            "総トークン数",
            "評価",
            "コメント",
        ]

        # Collect unique group names, document, FAQ, and web reference columns
        doc_columns = []
        group_names = []
        faq_columns = []
        web_columns = []
        attachment_columns = []

        for item in data:
            for key in item:
                if key.startswith("ドキュメント参照元") and key not in doc_columns:
                    doc_columns.append(key)
                elif key.startswith("所属グループ") and key not in group_names:
                    group_names.append(key)
                elif key.startswith("FAQ参照元") and key not in faq_columns:
                    faq_columns.append(key)
                elif key.startswith("Web参照元") and key not in web_columns:
                    web_columns.append(key)
                elif key.startswith("添付ファイル") and key not in attachment_columns:
                    attachment_columns.append(key)

        # Combine column order
        column_order.extend(doc_columns)
        column_order.extend(group_names)
        column_order.extend(faq_columns)
        column_order.extend(web_columns)
        column_order.extend(attachment_columns)

        return column_order

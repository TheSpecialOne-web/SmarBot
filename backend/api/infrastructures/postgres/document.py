from datetime import datetime, timezone

from sqlalchemy import and_, delete, select, update
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.orm import Session

from api.domain.models import (
    bot as bot_domain,
    document as document_domain,
    document_folder as document_folder_domain,
)
from api.domain.models.document.feedback import DocumentFeedback
from api.domain.models.user import Id as UserId
from api.libs.exceptions import NotFound

from .models.document import Document
from .models.document_folder import DocumentFolder
from .models.document_folder_path import DocumentFolderPath
from .models.user_document import UserDocument


class DocumentRepository(document_domain.IDocumentRepository):
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        bot_id: bot_domain.Id,
        parent_document_folder_id: document_folder_domain.Id,
        document: document_domain.DocumentForCreate,
    ) -> document_domain.Document:
        new_document = Document.from_domain(
            domain_model=document,
            bot_id=bot_id,
            document_folder_id=parent_document_folder_id,
        )
        try:
            self.session.add(new_document)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

        return new_document.to_domain()

    def bulk_create_external_documents(
        self,
        bot_id: bot_domain.Id,
        parent_document_folder_id: document_folder_domain.Id,
        external_documents: list[document_domain.ExternalDocumentForCreate],
    ) -> list[document_domain.Document]:
        new_external_documents = [
            Document.from_external_domain(
                domain_model=external_document, bot_id=bot_id, document_folder_id=parent_document_folder_id
            )
            for external_document in external_documents
        ]

        try:
            self.session.add_all(new_external_documents)
            self.session.commit()
            return [new_external_document.to_domain() for new_external_document in new_external_documents]
        except Exception as e:
            self.session.rollback()
            raise e

    def find_by_id_and_bot_id(self, id: document_domain.Id, bot_id: bot_domain.Id) -> document_domain.Document:
        document = (
            self.session.execute(
                select(Document)
                .join(DocumentFolder, Document.document_folder_id == DocumentFolder.id)
                .where(DocumentFolder.bot_id == bot_id.value)
                .where(Document.id == id.value)
            )
            .scalars()
            .first()
        )
        if not document:
            raise NotFound("ドキュメントが存在しません。")
        return document.to_domain()

    def find_by_bot_id(self, bot_id: bot_domain.Id) -> list[document_domain.Document]:
        documents = (
            self.session.execute(
                select(Document)
                .join(DocumentFolder, Document.document_folder_id == DocumentFolder.id)
                .where(DocumentFolder.bot_id == bot_id.value)
            )
            .scalars()
            .all()
        )
        return [document.to_domain() for document in documents]

    def find_by_bot_id_and_parent_document_folder_id_and_name(
        self, bot_id: bot_domain.Id, parent_document_folder_id: document_folder_domain.Id, name: document_domain.Name
    ) -> document_domain.Document:
        document = self.session.execute(
            select(Document)
            .join(DocumentFolder, Document.document_folder_id == DocumentFolder.id)
            .where(
                Document.basename == name.value,
                DocumentFolder.bot_id == bot_id.value,
                Document.document_folder_id == parent_document_folder_id.root,
            )
        ).scalar_one_or_none()
        if not document:
            raise NotFound("ドキュメントが存在しません。")
        return document.to_domain()

    def find_by_parent_document_folder_id(
        self, bot_id: bot_domain.Id, parent_document_folder_id: document_folder_domain.Id
    ) -> list[document_domain.Document]:
        stmt = (
            select(Document)
            .join(DocumentFolder, Document.document_folder_id == DocumentFolder.id)
            .where(DocumentFolder.bot_id == bot_id.value, DocumentFolder.id == parent_document_folder_id.root)
        )
        documents = self.session.execute(stmt).scalars().all()
        return [document.to_domain() for document in documents]

    def update(self, document: document_domain.Document) -> None:
        try:
            update_stmt = (
                update(Document)
                .where(Document.id == document.id.value)
                .values(
                    basename=document.name.value,
                    memo=document.memo.value if document.memo else None,
                    status=document.status.value,
                    storage_usage=document.storage_usage.root if document.storage_usage else None,
                    document_folder_id=document.document_folder_id.root,
                )
            )
            self.session.execute(update_stmt)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def bulk_update(self, documents: list[document_domain.Document]) -> None:
        existing_documents = (
            self.session.execute(
                select(Document).where(Document.id.in_([document.id.value for document in documents]))
            )
            .scalars()
            .all()
        )

        for document in documents:
            existing_document = next(
                (
                    existing_document
                    for existing_document in existing_documents
                    if existing_document.id == document.id.value
                ),
                None,
            )
            if not existing_document:
                continue

            if document.memo:
                existing_document.memo = document.memo.value
            existing_document.status = document.status.value

        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def delete(self, id: document_domain.Id) -> None:
        try:
            document = self.session.execute(select(Document).filter_by(id=id.value)).scalars().first()
            if not document:
                raise NotFound("ドキュメントが存在しません。")
            document.deleted_at = datetime.utcnow()
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def delete_by_bot_id(self, bot_id: bot_domain.Id) -> None:
        now = datetime.now(timezone.utc)

        stmt = (
            update(Document)
            .where(Document.document_folder_id == DocumentFolder.id)
            .where(DocumentFolder.bot_id == bot_id.value)
            .values(deleted_at=now)
        )

        try:
            self.session.execute(stmt)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def delete_by_folder_ids(
        self, bot_id: bot_domain.Id, document_folder_ids: list[document_folder_domain.Id]
    ) -> None:
        now = datetime.now(timezone.utc)

        stmt = (
            update(Document)
            .where(
                Document.document_folder_id.in_([id.root for id in document_folder_ids]),
                Document.document_folder_id == DocumentFolder.id,
                DocumentFolder.bot_id == bot_id.value,
            )
            .values(deleted_at=now)
        )

        try:
            self.session.execute(stmt)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def hard_delete_by_document_folder_ids(self, document_folder_ids: list[document_folder_domain.Id]) -> None:
        document_folder_id_values = [document_folder_id.root for document_folder_id in document_folder_ids]
        try:
            self.session.execute(
                delete(Document)
                .where(Document.document_folder_id.in_(document_folder_id_values))
                .where(Document.deleted_at.isnot(None))
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def hard_delete_by_bot_ids(self, bot_ids: list[bot_domain.Id]) -> None:
        """document_folder_id の入っていない documents のレコードを bot_id で削除する

        Args:
            bot_ids (list[bot_domain.Id]): 削除対象の bot_id のリスト
        """
        try:
            self.session.execute(
                delete(Document)
                .where(Document.bot_id.in_([bot_id.value for bot_id in bot_ids]))
                .where(Document.document_folder_id.is_(None))
                .where(Document.deleted_at.isnot(None))
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def find_by_ids_and_bot_id(
        self, bot_id: bot_domain.Id, document_ids: list[document_domain.Id]
    ) -> list[document_domain.Document]:
        documents = (
            self.session.execute(
                select(Document)
                .join(DocumentFolder, Document.document_folder_id == DocumentFolder.id)
                .where(
                    DocumentFolder.bot_id == bot_id.value,
                    Document.id.in_([id.value for id in document_ids]),
                )
            )
            .scalars()
            .all()
        )
        return [document.to_domain() for document in documents]

    def find_by_bot_id_and_parent_document_folder_id(
        self, bot_id: bot_domain.Id, parent_document_folder_id: document_folder_domain.Id
    ) -> list[document_domain.Document]:
        documents = (
            self.session.execute(
                select(Document)
                .where(Document.document_folder_id == parent_document_folder_id.root)
                .join(DocumentFolder, Document.document_folder_id == DocumentFolder.id)
                .where(DocumentFolder.bot_id == bot_id.value)
            )
            .scalars()
            .all()
        )
        return [document.to_domain() for document in documents]

    def find_feedback_by_id_and_user_id(self, id: document_domain.Id, user_id: UserId) -> DocumentFeedback:
        stmt = (
            select(UserDocument)
            .where(UserDocument.document_id == id.value)
            .where(UserDocument.user_id == user_id.value)
        )
        try:
            user_document = self.session.execute(stmt).scalar_one()
            return user_document.to_domain()
        except NoResultFound:
            raise NotFound("フィードバックが見つかりませんでした。")
        except MultipleResultsFound:
            raise Exception("複数のフィードバックが見つかりました")

    def find_feedbacks_by_ids_and_user_id(
        self, ids: list[document_domain.Id], user_id: UserId
    ) -> list[DocumentFeedback]:
        stmt = (
            select(UserDocument)
            .where(UserDocument.document_id.in_([id.value for id in ids]))
            .where(UserDocument.user_id == user_id.value)
        )
        user_documents = self.session.execute(stmt).scalars().all()
        return [user_document.to_domain() for user_document in user_documents]

    def create_feedback(self, feedback: DocumentFeedback) -> DocumentFeedback:
        new_user_document = UserDocument.from_domain(feedback)
        try:
            self.session.add(new_user_document)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

        return new_user_document.to_domain()

    def update_feedback(self, feedback: DocumentFeedback) -> None:
        try:
            self.session.execute(
                update(UserDocument)
                .where(UserDocument.document_id == feedback.document_id.value)
                .where(UserDocument.user_id == feedback.user_id.value)
                .values(evaluation=feedback.evaluation.value if feedback.evaluation is not None else None)
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def find_all_descendants_documents_by_ancestor_folder_id(
        self,
        bot_id: bot_domain.Id,
        ancestor_folder_id: document_folder_domain.Id,
    ) -> list[document_domain.Document]:
        # フォルダ配下の全ドキュメントを取得
        stmt = (
            select(Document)
            .join(
                DocumentFolderPath,
                and_(
                    DocumentFolderPath.descendant_document_folder_id == Document.document_folder_id,
                    DocumentFolderPath.ancestor_document_folder_id == ancestor_folder_id.root,
                ),
            )
            .join(
                DocumentFolder,
                DocumentFolder.id == DocumentFolderPath.descendant_document_folder_id,
            )
            .where(DocumentFolder.bot_id == bot_id.value)
            .where(Document.status != document_domain.Status.DELETING.value)
        )

        results = self.session.execute(stmt).scalars().all()

        # ドメインオブジェクトに変換
        return [doc.to_domain() for doc in results]

    def find_documents_with_ancestor_folders_by_ids(
        self,
        bot_id: bot_domain.Id,
        ids: list[document_domain.Id],
    ) -> list[document_domain.DocumentWithAncestorFolders]:
        # documentとfolderのペアの形式で祖先フォルダを全て取得 ex) (Document1, Folder1), (Document1, Folder2), (Document2, Folder1)
        stmt = (
            select(
                Document,
                DocumentFolder,
            )
            # documentが属しているフォルダがdescendantであるDocumentFolderPathを取得
            .join(
                DocumentFolderPath,
                Document.document_folder_id == DocumentFolderPath.descendant_document_folder_id,
            )
            # DocumentFolderPath の ancestor_document_folder_id を使って実際のフォルダ情報を取得
            .join(
                DocumentFolder,
                DocumentFolder.id == DocumentFolderPath.ancestor_document_folder_id,
            )
            .where(Document.id.in_([id.value for id in ids]))
            .where(DocumentFolder.bot_id == bot_id.value)
            # パスの長さでソート（浅い順）
            .order_by(Document.id, DocumentFolderPath.path_length.desc())
        )

        results = self.session.execute(stmt).all()
        documents_map: dict[int, document_domain.DocumentWithAncestorFolders] = {}

        # 結果の処理
        for result in results:
            document: Document = result[0]
            folder: DocumentFolder = result[1]
            if document.id not in documents_map:
                doc_domain = document.to_domain()
                documents_map[document.id] = document_domain.DocumentWithAncestorFolders(
                    id=doc_domain.id,
                    name=doc_domain.name,
                    memo=doc_domain.memo,
                    status=doc_domain.status,
                    storage_usage=doc_domain.storage_usage,
                    creator_id=doc_domain.creator_id,
                    created_at=doc_domain.created_at,
                    file_extension=doc_domain.file_extension,
                    document_folder_id=doc_domain.document_folder_id,
                    external_id=doc_domain.external_id,
                    external_updated_at=doc_domain.external_updated_at,
                    ancestor_folders=[],
                )
            order = len(documents_map[document.id].ancestor_folders)
            folder_with_order = folder.to_domain_with_order(order)
            documents_map[document.id].ancestor_folders.append(folder_with_order)

        return list(documents_map.values())

    def find_with_ancestor_folders_by_id(
        self,
        bot_id: bot_domain.Id,
        id: document_domain.Id,
    ) -> document_domain.DocumentWithAncestorFolders:
        result = self.find_documents_with_ancestor_folders_by_ids(bot_id, [id])

        if len(result) != 1:
            raise Exception("ドキュメントの取得に失敗しました。")
        return result[0]

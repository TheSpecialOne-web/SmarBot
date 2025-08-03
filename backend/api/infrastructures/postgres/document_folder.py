from datetime import datetime, timezone
import uuid

from sqlalchemy import and_, delete, func, select
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.orm import Session, joinedload

from api.domain.models import document_folder as document_folder_domain
from api.domain.models.bot import Id as BotId
from api.domain.models.document_folder import (
    DocumentFolderWithAncestors,
    DocumentFolderWithDescendants,
    external_data_connection as external_document_folder_domain,
)
from api.domain.models.document_folder.document_folder import DocumentFolderWithOrder
from api.libs.exceptions import BadRequest, NotFound

from .models.document_folder import DocumentFolder
from .models.document_folder_path import DocumentFolderPath


class DocumentFolderRepository(document_folder_domain.IDocumentFolderRepository):
    def __init__(self, session: Session):
        self.session = session

    def find_root_document_folder_by_bot_id(self, bot_id: BotId) -> document_folder_domain.DocumentFolder:
        stmt = (
            select(DocumentFolder)
            .where(DocumentFolder.bot_id == bot_id.value)
            # ルートフォルダは、DocumentFolderPathのpath_lengthが0のDocumentFolderPathを1つだけ持つ
            .join(DocumentFolderPath, DocumentFolderPath.descendant_document_folder_id == DocumentFolder.id)
            .group_by(DocumentFolder.id)
            .having(func.count(DocumentFolderPath.id) == 1)
        )
        try:
            document_folder = self.session.execute(stmt).scalar_one()
            return document_folder.to_domain()
        except NoResultFound:
            raise NotFound(f"アシスタントID {bot_id.value} のルートフォルダが見つかりません")
        except MultipleResultsFound:
            raise Exception(f"アシスタントID {bot_id.value} のルートフォルダが複数見つかりました")

    def find_by_id_and_bot_id(
        self, document_folder_id: document_folder_domain.Id, bot_id: BotId
    ) -> document_folder_domain.DocumentFolder:
        stmt = select(DocumentFolder).where(
            DocumentFolder.id == document_folder_id.root, DocumentFolder.bot_id == bot_id.value
        )
        document_folder = self.session.execute(stmt).scalars().first()
        if document_folder is None:
            raise NotFound("指定されたフォルダは存在しません")
        return document_folder.to_domain()

    def find_by_bot_ids(
        self, bot_ids: list[BotId], include_deleted: bool = False
    ) -> list[document_folder_domain.DocumentFolder]:
        bot_id_values = [bot_id.value for bot_id in bot_ids]
        document_folders = (
            self.session.execute(
                select(DocumentFolder)
                .where(DocumentFolder.bot_id.in_(bot_id_values))
                .execution_options(include_deleted=include_deleted)
            )
            .scalars()
            .all()
        )
        return [document_folder.to_domain() for document_folder in document_folders]

    def find_by_parent_document_folder_id(
        self, bot_id: BotId, parent_document_folder_id: document_folder_domain.Id
    ) -> list[document_folder_domain.DocumentFolder]:
        stmt = (
            select(DocumentFolder)
            .where(DocumentFolder.bot_id == bot_id.value)
            .outerjoin(DocumentFolderPath, DocumentFolderPath.descendant_document_folder_id == DocumentFolder.id)
            .where(DocumentFolderPath.ancestor_document_folder_id == parent_document_folder_id.root)
            .where(DocumentFolderPath.path_length == 1)
        )
        document_folders = self.session.execute(stmt).scalars().all()
        return [document_folder.to_domain() for document_folder in document_folders]

    def find_descendants_by_id(
        self, bot_id: BotId, id: document_folder_domain.Id
    ) -> list[document_folder_domain.DocumentFolder]:
        stmt = (
            select(DocumentFolder)
            .where(DocumentFolder.bot_id == bot_id.value)
            .join(DocumentFolderPath, DocumentFolderPath.descendant_document_folder_id == DocumentFolder.id)
            .where(DocumentFolderPath.ancestor_document_folder_id == id.root)
            .where(DocumentFolderPath.path_length > 0)
            .order_by(DocumentFolderPath.path_length.desc())
        )
        document_folders = self.session.execute(stmt).scalars().all()
        return [document_folder.to_domain() for document_folder in document_folders]

    # TODO: 2つ以上のケースはないので、one_or_none にする
    def find_by_parent_document_folder_id_and_name(
        self,
        parent_document_folder_id: document_folder_domain.Id,
        name: document_folder_domain.Name,
    ) -> list[document_folder_domain.DocumentFolder]:
        stmt = (
            select(DocumentFolder)
            .outerjoin(DocumentFolderPath, DocumentFolderPath.descendant_document_folder_id == DocumentFolder.id)
            .where(DocumentFolderPath.ancestor_document_folder_id == parent_document_folder_id.root)
            .where(DocumentFolderPath.path_length == 1)
            .where(DocumentFolder.name == name.root)
        )
        document_folders = self.session.execute(stmt).scalars().all()
        return [document_folder.to_domain() for document_folder in document_folders]

    def find_with_ancestors_by_id_and_bot_id(
        self, id: document_folder_domain.Id, bot_id: BotId
    ) -> DocumentFolderWithAncestors:
        # サブクエリ: 対象フォルダとその祖先のIDと階層順序を取得
        ancestor_subquery = (
            select(DocumentFolderPath).where(DocumentFolderPath.descendant_document_folder_id == id.root).subquery()
        )

        # メインクエリ
        stmt = (
            select(DocumentFolder)
            .join(ancestor_subquery, DocumentFolder.id == ancestor_subquery.c.ancestor_document_folder_id)
            .where(DocumentFolder.bot_id == bot_id.value)
            .order_by(ancestor_subquery.c.path_length.desc())
        )

        result = self.session.execute(stmt).scalars().all()

        if len(result) == 0:
            raise NotFound("指定されたフォルダは存在しません")

        ancestors = [df.to_domain_with_order(index) for index, df in enumerate(result[:-1])]
        target = result[-1].to_domain()

        return DocumentFolderWithAncestors(
            id=target.id,
            name=target.name,
            external_id=target.external_id,
            external_type=target.external_type,
            created_at=target.created_at,
            ancestor_folders=ancestors,
        )

    def find_with_descendants_by_id_and_bot_id(
        self, id: document_folder_domain.Id, bot_id: BotId
    ) -> DocumentFolderWithDescendants:
        # サブクエリ: 対象フォルダとその子孫のIDと階層順序を取得
        descendant_subquery = (
            select(DocumentFolderPath).where(DocumentFolderPath.ancestor_document_folder_id == id.root).subquery()
        )

        # メインクエリ
        stmt = (
            select(DocumentFolder)
            .join(descendant_subquery, DocumentFolder.id == descendant_subquery.c.descendant_document_folder_id)
            .where(DocumentFolder.bot_id == bot_id.value)
            .order_by(descendant_subquery.c.path_length.asc())
        )

        result = self.session.execute(stmt).scalars().all()

        if len(result) == 0:
            raise NotFound("指定されたフォルダは存在しません")

        # path_lengthの昇順に並んでいるので、最初の要素が対象フォルダ、それ以外が子孫フォルダ
        descendants = [df.to_domain() for df in result[1:]]
        target = result[0].to_domain()

        return DocumentFolderWithDescendants(
            id=target.id,
            name=target.name,
            created_at=target.created_at,
            descendant_folders=descendants,
        )

    def find_external_document_folder_by_id_and_bot_id(
        self, id: document_folder_domain.Id, bot_id: BotId
    ) -> external_document_folder_domain.ExternalDocumentFolder:
        stmt = select(DocumentFolder).where(DocumentFolder.id == id.root).where(DocumentFolder.bot_id == bot_id.value)
        document_folder = self.session.execute(stmt).scalars().one_or_none()
        if document_folder is None:
            raise NotFound("指定されたフォルダは存在しません")
        return document_folder.to_external_domain()

    def create(
        self,
        bot_id: BotId,
        parent_document_folder_id: document_folder_domain.Id,
        document_folder: document_folder_domain.DocumentFolderForCreate,
    ) -> document_folder_domain.DocumentFolder:
        # create document_folder
        new_document_folder = DocumentFolder.from_domain(
            domain_model=document_folder,
            bot_id=bot_id,
        )

        # create document_folder_paths
        find_by_descendant_document_folder_id_stmt = select(DocumentFolderPath).where(
            DocumentFolderPath.descendant_document_folder_id == parent_document_folder_id.root
        )
        document_folder_paths = self.session.execute(find_by_descendant_document_folder_id_stmt).scalars().all()
        new_document_folder_paths = [
            DocumentFolderPath(
                id=uuid.uuid4(),
                ancestor_document_folder_id=document_folder_path.ancestor_document_folder_id,
                descendant_document_folder_id=new_document_folder.id,
                path_length=document_folder_path.path_length + 1,
            )
            for document_folder_path in document_folder_paths
        ]
        new_document_folder_paths.append(
            DocumentFolderPath(
                id=uuid.uuid4(),
                ancestor_document_folder_id=new_document_folder.id,
                descendant_document_folder_id=new_document_folder.id,
                path_length=0,
            )
        )

        try:
            self.session.add(new_document_folder)
            self.session.flush()
            self.session.add_all(new_document_folder_paths)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

        return new_document_folder.to_domain()

    def create_external_document_folder(
        self,
        bot_id: BotId,
        parent_document_folder_id: document_folder_domain.Id,
        external_document_folder: document_folder_domain.ExternalDocumentFolderForCreate,
    ) -> document_folder_domain.DocumentFolder:
        new_document_folder = DocumentFolder.from_external_domain(
            domain_model=external_document_folder,
            bot_id=bot_id,
        )

        # create document_folder_paths
        find_document_folder_paths_by_descendant_document_folder_id_stmt = select(DocumentFolderPath).where(
            DocumentFolderPath.descendant_document_folder_id == parent_document_folder_id.root
        )
        document_folder_paths = (
            self.session.execute(find_document_folder_paths_by_descendant_document_folder_id_stmt).scalars().all()
        )
        new_document_folder_paths = [
            DocumentFolderPath(
                id=uuid.uuid4(),
                ancestor_document_folder_id=document_folder_path.ancestor_document_folder_id,
                descendant_document_folder_id=new_document_folder.id,
                path_length=document_folder_path.path_length + 1,
            )
            for document_folder_path in document_folder_paths
        ]
        new_document_folder_paths.append(
            DocumentFolderPath(
                id=uuid.uuid4(),
                ancestor_document_folder_id=new_document_folder.id,
                descendant_document_folder_id=new_document_folder.id,
                path_length=0,
            )
        )

        try:
            self.session.add(new_document_folder)
            self.session.flush()
            self.session.add_all(new_document_folder_paths)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

        return new_document_folder.to_domain()

    def update(
        self,
        bot_id: BotId,
        document_folder: document_folder_domain.DocumentFolder,
    ) -> document_folder_domain.DocumentFolder:
        stmt = (
            select(DocumentFolder)
            .where(DocumentFolder.id == document_folder.id.root)
            .where(DocumentFolder.bot_id == bot_id.value)
        )
        df = self.session.execute(stmt).scalars().first()
        if df is None:
            raise NotFound("指定されたフォルダは存在しません")

        if document_folder.name is None:
            raise BadRequest("ルートフォルダ以外は名前が必須です")
        try:
            df.name = document_folder.name.root
            self.session.commit()
            return df.to_domain()
        except Exception as e:
            self.session.rollback()
            raise e

    def delete_by_ids(self, bot_id: BotId, document_folder_ids: list[document_folder_domain.Id]) -> None:
        # 削除する document_folder を取得
        df_stmt = (
            select(DocumentFolder)
            .where(DocumentFolder.id.in_([df_id.root for df_id in document_folder_ids]))
            .where(DocumentFolder.bot_id == bot_id.value)
        )
        document_folders = self.session.execute(df_stmt).scalars().all()

        # 削除する document_folder に紐づく document_folder_paths を取得
        dfp_stmt = select(DocumentFolderPath).where(
            DocumentFolderPath.descendant_document_folder_id.in_([df_id.root for df_id in document_folder_ids])
        )
        document_folder_paths = self.session.execute(dfp_stmt).scalars().all()

        now = datetime.now()
        try:
            for document_folder_path in document_folder_paths:
                document_folder_path.deleted_at = now
            for document_folder in document_folders:
                document_folder.deleted_at = now
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def create_root_document_folder(
        self, bot_id: BotId, root_document_folder_for_create: document_folder_domain.RootDocumentFolderForCreate
    ) -> document_folder_domain.DocumentFolder:
        root_document_folder = DocumentFolder.from_domain(
            domain_model=root_document_folder_for_create,
            bot_id=bot_id,
        )
        root_document_folder_path = DocumentFolderPath(
            id=uuid.uuid4(),
            ancestor_document_folder_id=root_document_folder.id,
            descendant_document_folder_id=root_document_folder.id,
            path_length=0,
        )
        try:
            self.session.add(root_document_folder)
            self.session.flush()
            self.session.add(root_document_folder_path)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

        return root_document_folder.to_domain()

    def delete_by_bot_id(self, bot_id: BotId) -> None:
        folders = (
            self.session.execute(
                select(DocumentFolder)
                .join(DocumentFolderPath, DocumentFolder.id == DocumentFolderPath.descendant_document_folder_id)
                .where(DocumentFolder.bot_id == bot_id.value)
                .options(joinedload(DocumentFolder.descendants))
            )
            .unique()
            .scalars()
            .all()
        )

        now = datetime.now(timezone.utc)
        for folder in folders:
            folder.deleted_at = now
            for descendant in folder.descendants:
                descendant.deleted_at = now

        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def hard_delete_by_bot_ids(self, bot_ids: list[BotId]) -> None:
        bot_id_values = [bot_id.value for bot_id in bot_ids]
        try:
            self.session.execute(
                delete(DocumentFolder)
                .where(DocumentFolder.bot_id.in_(bot_id_values))
                .where(DocumentFolder.deleted_at.isnot(None))
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def move_document_folder(
        self,
        bot_id: BotId,
        document_folder_id: document_folder_domain.Id,
        new_parent_document_folder_id: document_folder_domain.Id,
    ) -> None:
        try:
            document_folder_with_descendants_list = self._find_descendants_with_order_by_id_and_bot_id(
                document_folder_id, bot_id
            )
            folder_ids_to_move = [folder.id for folder in document_folder_with_descendants_list]

            # 移動対象のフォルダとその子孫の以前の DocumentFolderPath を物理削除
            self._delete_document_folder_path(self.session, folder_ids_to_move)

            new_parent_document_folder_with_ansestors_list = self._find_ancestors_with_order_by_id_and_bot_id(
                new_parent_document_folder_id, bot_id
            )

            # フォルダパスを更新
            new_document_folder_paths = []
            new_parent_document_folder_order = new_parent_document_folder_with_ansestors_list[-1].order.root
            for df in document_folder_with_descendants_list:
                for npdf in new_parent_document_folder_with_ansestors_list:
                    path_length = df.order.root - npdf.order.root + new_parent_document_folder_order + 1
                    new_document_folder_paths.append(
                        DocumentFolderPath(
                            id=uuid.uuid4(),
                            ancestor_document_folder_id=npdf.id.root,
                            descendant_document_folder_id=df.id.root,
                            path_length=path_length,
                        )
                    )

            self.session.add_all(new_document_folder_paths)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def _find_ancestors_with_order_by_id_and_bot_id(
        self, id: document_folder_domain.Id, bot_id: BotId
    ) -> list[DocumentFolderWithOrder]:
        # サブクエリ: 対象フォルダとその祖先のIDと階層順序を取得
        ancestor_subquery = (
            select(DocumentFolderPath).where(DocumentFolderPath.descendant_document_folder_id == id.root).subquery()
        )

        # メインクエリ
        stmt = (
            select(DocumentFolder)
            .join(ancestor_subquery, DocumentFolder.id == ancestor_subquery.c.ancestor_document_folder_id)
            .where(DocumentFolder.bot_id == bot_id.value)
            .order_by(ancestor_subquery.c.path_length.desc())
        )

        result = self.session.execute(stmt).scalars().all()

        if len(result) == 0:
            raise NotFound("指定されたフォルダは存在しません")

        ancestors = [df.to_domain_with_order(index) for index, df in enumerate(result)]

        return ancestors

    def _find_descendants_with_order_by_id_and_bot_id(
        self, id: document_folder_domain.Id, bot_id: BotId
    ) -> list[DocumentFolderWithOrder]:
        # 対象フォルダとその子孫のIDと階層順序を取得するサブクエリ
        descendant_subquery = (
            select(DocumentFolderPath).where(DocumentFolderPath.ancestor_document_folder_id == id.root).subquery()
        )

        # メインクエリ
        stmt = (
            select(DocumentFolder, descendant_subquery.c.path_length)
            .join(descendant_subquery, DocumentFolder.id == descendant_subquery.c.descendant_document_folder_id)
            .where(DocumentFolder.bot_id == bot_id.value)
            .order_by(descendant_subquery.c.path_length.asc())
        )

        rows = self.session.execute(stmt).all()

        if not rows:
            raise NotFound("指定されたフォルダは存在しません")

        descendants = []
        current_path_length = None
        current_order = -1

        # 子孫フォルダのOrderを計算
        for row in rows:
            folder: DocumentFolder = row[0]
            path_length: int = row[1]

            if current_path_length != path_length:
                current_path_length = path_length
                current_order += 1

            descendants.append(folder.to_domain_with_order(current_order))

        return descendants

    def _delete_document_folder_path(
        self, session: Session, folder_ids_to_move: list[document_folder_domain.Id]
    ) -> None:
        for folder_id in folder_ids_to_move:
            stmt = select(DocumentFolderPath).where(
                and_(
                    DocumentFolderPath.descendant_document_folder_id == folder_id.root,
                    DocumentFolderPath.ancestor_document_folder_id.notin_([f_id.root for f_id in folder_ids_to_move]),
                )
            )
            document_folder_paths = session.execute(stmt).scalars().all()

            for document_folder_path in document_folder_paths:
                session.delete(document_folder_path)

        session.flush()

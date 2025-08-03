from uuid import UUID, uuid4

from pydantic import RootModel


# Id クラスを定義
class Id(RootModel[UUID]):
    root: UUID


def create_id() -> Id:
    return Id(root=uuid4())

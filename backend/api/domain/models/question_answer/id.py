import uuid
from uuid import UUID

from pydantic import RootModel


# Id クラスを定義
class Id(RootModel[UUID]):
    root: UUID

    def to_index_filter(self) -> str:
        return f"question_answer_id eq '{self.root!s}'"


def create_id() -> Id:
    return Id(root=uuid.uuid4())

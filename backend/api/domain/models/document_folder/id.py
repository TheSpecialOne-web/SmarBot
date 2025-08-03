from uuid import UUID, uuid4

from pydantic import RootModel


class Id(RootModel[UUID]):
    root: UUID

    def to_index_filter(self) -> str:
        return f"document_folder_id eq '{self.root!s}'"


def create_id() -> Id:
    return Id(root=uuid4())

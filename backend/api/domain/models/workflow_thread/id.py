from uuid import UUID, uuid4

from pydantic import RootModel


class Id(RootModel[UUID]):
    root: UUID


def create_id() -> Id:
    return Id(root=uuid4())

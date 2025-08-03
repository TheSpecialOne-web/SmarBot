from uuid import UUID

from pydantic import RootModel


class Id(RootModel[UUID]):
    root: UUID

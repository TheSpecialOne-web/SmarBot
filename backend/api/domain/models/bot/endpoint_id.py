from uuid import UUID, uuid4

from pydantic import RootModel


# Id クラスを定義
class EndpointId(RootModel[UUID]):
    root: UUID


def create_endpoint_id() -> EndpointId:
    return EndpointId(root=uuid4())

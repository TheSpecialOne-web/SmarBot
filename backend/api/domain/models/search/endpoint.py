from pydantic import BaseModel, RootModel, StrictInt, StrictStr


class Endpoint(RootModel):
    root: StrictStr


class Priority(RootModel):
    root: StrictInt


class EndpointWithPriority(BaseModel):
    endpoint: Endpoint
    priority: Priority


class EndpointsWithPriority(RootModel):
    root: list[EndpointWithPriority]

    def get_most_prioritized_endpoint(self) -> Endpoint:
        return max(self.root, key=lambda x: x.priority.root).endpoint

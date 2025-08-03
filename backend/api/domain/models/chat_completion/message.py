from pydantic import BaseModel, RootModel

from .content import Content
from .role import Role


class Message(BaseModel):
    role: Role
    content: Content


class Messages(RootModel):
    root: list[Message]

    def to_json(self):
        return [message.model_dump_json() for message in self.root]

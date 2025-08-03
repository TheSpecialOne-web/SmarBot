from enum import Enum

from pydantic import RootModel


class ActionEnum(Enum):
    READ = "read"
    WRITE = "write"
    ALL = "all"


class Action(RootModel[ActionEnum]):
    root: ActionEnum

    @classmethod
    def from_str(cls, action: str) -> "Action":
        if action == ActionEnum.READ.value:
            return Action(root=ActionEnum.READ)
        if action == ActionEnum.WRITE.value:
            return Action(root=ActionEnum.WRITE)
        if action == ActionEnum.ALL.value:
            return Action(root=ActionEnum.ALL)
        raise ValueError(f"Invalid action: {action}")

    def to_str(self) -> str:
        return self.root.value

    @property
    def priority(self) -> int:
        if self.root == ActionEnum.READ:
            return 1
        if self.root == ActionEnum.WRITE:
            return 2
        if self.root == ActionEnum.ALL:
            return 3
        raise ValueError(f"Invalid action: {self.root}")

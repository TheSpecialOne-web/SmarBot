from typing import Any

from pydantic import BaseModel


class InputItem(BaseModel):
    key: str
    value: Any


class Input(BaseModel):
    items: list[InputItem]

    def get_value(self, key: str) -> Any:
        for item in self.items:
            if item.key == key:
                return item.value
        raise ValueError(f"Key '{key}' not found in input")

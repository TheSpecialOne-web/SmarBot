from typing import Any

from pydantic import BaseModel


class OutputItem(BaseModel):
    key: str
    value: Any


class Output(BaseModel):
    items: list[OutputItem]

    def get_value(self, key: str) -> Any:
        for item in self.items:
            if item.key == key:
                return item.value
        raise ValueError(f"Key '{key}' not found in output")

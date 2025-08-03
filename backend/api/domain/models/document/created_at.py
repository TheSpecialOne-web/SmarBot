from datetime import datetime

from pydantic import BaseModel


class CreatedAt(BaseModel):
    value: datetime

    def formatted(self) -> str:
        return self.value.strftime("%Y-%m-%dT%H:%M:%SZ")

from pydantic import BaseModel, StrictInt


class Id(BaseModel):
    value: StrictInt

    def to_index_filter(self):
        return f"bot_id eq {self.value}"

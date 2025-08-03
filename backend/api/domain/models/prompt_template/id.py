from pydantic import BaseModel, StrictInt


class Id(BaseModel):
    value: StrictInt

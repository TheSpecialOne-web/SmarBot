from pydantic import BaseModel, StrictStr


class Value(BaseModel):
    value: StrictStr

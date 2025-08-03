from pydantic import BaseModel, StrictStr


class Name(BaseModel):
    value: StrictStr

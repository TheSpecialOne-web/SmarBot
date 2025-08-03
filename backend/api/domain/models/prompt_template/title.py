from pydantic import BaseModel, StrictStr


class Title(BaseModel):
    value: StrictStr

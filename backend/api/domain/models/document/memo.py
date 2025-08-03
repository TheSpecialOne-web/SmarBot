from pydantic import BaseModel, StrictStr


class Memo(BaseModel):
    value: StrictStr

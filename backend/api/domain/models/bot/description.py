from pydantic import BaseModel, StrictStr


class Description(BaseModel):
    value: StrictStr

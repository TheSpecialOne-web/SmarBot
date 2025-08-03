from pydantic import BaseModel, StrictStr


class SignedUrl(BaseModel):
    value: StrictStr

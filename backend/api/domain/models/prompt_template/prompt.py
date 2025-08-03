from pydantic import BaseModel, StrictStr


class Prompt(BaseModel):
    value: StrictStr

from pydantic import BaseModel, StrictStr


class ExampleQuestion(BaseModel):
    value: StrictStr

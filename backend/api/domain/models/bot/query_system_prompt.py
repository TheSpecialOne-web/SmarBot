from pydantic import RootModel, StrictStr


class QuerySystemPrompt(RootModel):
    root: StrictStr

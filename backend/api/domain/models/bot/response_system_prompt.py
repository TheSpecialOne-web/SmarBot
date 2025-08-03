from pydantic import RootModel, StrictStr


class ResponseSystemPrompt(RootModel):
    root: StrictStr

    def is_empty(self) -> bool:
        return self.root == ""


class ResponseSystemPromptHidden(ResponseSystemPrompt):
    pass

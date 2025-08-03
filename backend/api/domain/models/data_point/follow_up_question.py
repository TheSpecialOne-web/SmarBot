from pydantic import RootModel, StrictStr


class FollowUpQuestion(RootModel):
    root: StrictStr

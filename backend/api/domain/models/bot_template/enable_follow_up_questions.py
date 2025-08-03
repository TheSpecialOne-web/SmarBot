from pydantic import RootModel, StrictBool


class EnableFollowUpQuestions(RootModel):
    root: StrictBool

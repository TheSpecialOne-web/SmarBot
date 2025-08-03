from pydantic import RootModel, StrictStr


class Answer(RootModel[StrictStr]):
    root: StrictStr

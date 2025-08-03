from pydantic import RootModel, StrictStr


class Question(RootModel[StrictStr]):
    root: StrictStr

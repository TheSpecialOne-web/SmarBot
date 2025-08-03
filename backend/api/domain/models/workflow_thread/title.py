from pydantic import RootModel, StrictStr


class Title(RootModel[StrictStr]):
    root: StrictStr

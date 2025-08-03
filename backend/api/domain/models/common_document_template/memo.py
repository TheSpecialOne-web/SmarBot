from pydantic import RootModel, StrictStr


class Memo(RootModel[StrictStr]):
    root: StrictStr

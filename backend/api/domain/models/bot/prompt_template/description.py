from pydantic import RootModel, StrictStr


class Description(RootModel):
    root: StrictStr

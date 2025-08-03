from pydantic import RootModel, StrictStr


class ChunkName(RootModel):
    root: StrictStr

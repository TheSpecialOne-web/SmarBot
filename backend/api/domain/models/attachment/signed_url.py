from pydantic import RootModel, StrictStr


class SignedUrl(RootModel):
    root: StrictStr

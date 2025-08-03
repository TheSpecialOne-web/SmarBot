from pydantic import RootModel, StrictBool


class IsLiked(RootModel):
    root: StrictBool

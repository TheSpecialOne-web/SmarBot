from pydantic import BaseModel, StrictStr


class IconColor(BaseModel):
    root: StrictStr

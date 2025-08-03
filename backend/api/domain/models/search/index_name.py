import re

from pydantic import RootModel, StrictStr, field_validator

from api.libs.exceptions import BadRequest


class IndexName(RootModel):
    root: StrictStr

    @field_validator("root", mode="before")
    @classmethod
    def validate_value(cls, v):
        # DBに空文字が入ってしまっているので、空文字は許容する
        if v == "":
            return v
        pattern = r"^[a-z0-9]([a-z0-9]|-(?=[a-z0-9])){0,126}[a-z0-9]$"
        if not re.match(pattern, v):
            raise BadRequest(f"不正なインデックス名です: {v}")
        return v

from pydantic import RootModel, StrictStr, field_validator


class Title(RootModel[StrictStr]):
    root: StrictStr = "無題のチャット"

    @field_validator("root")
    @classmethod
    def validate_root(cls, value: str) -> str:
        MAX_LENGTH = 255
        return value[:MAX_LENGTH]

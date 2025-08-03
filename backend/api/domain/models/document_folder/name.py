from pydantic import RootModel, StrictStr, model_validator

from api.libs.exceptions import BadRequest


class Name(RootModel[StrictStr]):
    root: StrictStr

    @model_validator(mode="after")
    def validate_reserved_chars(self):
        reserved_chars = "]:"
        if reserved_chars in self.root:
            raise BadRequest(f"以下の文字列はフォルダ名に使用できません。{reserved_chars}")
        return self

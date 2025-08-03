import os
import unicodedata

from pydantic import RootModel, StrictStr

from api.libs.exceptions import BadRequest
from api.libs.file import convert_halfwidth_to_fullwidth


class Basename(RootModel):
    root: StrictStr

    @classmethod
    def from_filename(cls, filename: str):
        try:
            name, _ = os.path.splitext(filename)
        except Exception:
            raise BadRequest("ファイル名が不正です。")
        if name == "":
            raise BadRequest("ファイル名が取得できません。")

        name = unicodedata.normalize("NFC", name)

        return cls(root=convert_halfwidth_to_fullwidth(name))

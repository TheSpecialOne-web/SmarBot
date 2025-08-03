from enum import Enum
import os

from api.libs.exceptions import BadRequest


class IconFileExtension(str, Enum):
    JPG = "jpg"
    JPEG = "jpeg"
    PNG = "png"

    @classmethod
    def from_filename(cls, filename: str) -> "IconFileExtension":
        try:
            _, ext = os.path.splitext(filename)
        except Exception:
            raise BadRequest("ファイル名が不正です。")
        if ext == "":
            raise BadRequest("ファイルの拡張子が取得できません。")
        ext_lower = ext[1:].lower()

        try:
            return cls(ext_lower)
        except Exception:
            raise BadRequest(
                f"ファイルの拡張子は {', '.join([e.value for e in IconFileExtension])} のいずれかである必要があります。"
            )

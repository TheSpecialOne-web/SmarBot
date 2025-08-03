import os
import unicodedata

from pydantic import RootModel, StrictStr

from api.libs.exceptions import BadRequest
from api.libs.file import convert_halfwidth_to_fullwidth

from .file_extension import FileExtension


class Name(RootModel):
    """アタッチメントの名前（拡張子なし）

    Attributes:
        value(str): アタッチメントの名前（拡張子なし）e.g. "sample"
    """

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


class BlobName(RootModel):
    """Blob Storage に保存する際の名前

    Attributes:
        value(str): Blob Storage に保存する際の名前 e.g. "sample.pdf"
    """

    root: StrictStr

    def file_extension(self):
        try:
            _, ext = os.path.splitext(self.root)
        except ValueError:
            raise BadRequest("ファイル名が不正です。")
        if ext == "":
            raise BadRequest("ファイル名に拡張子が含まれていません。")
        return FileExtension(ext[1:].lower())

    def to_content_disposition(self):
        extension = self.file_extension()

        if not extension.is_displayable():
            raise BadRequest("ファイルの拡張子がサポートされていません。")

        return f"inline; filename={self.root}"

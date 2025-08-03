import base64
import os
import unicodedata
import urllib.parse

from pydantic import BaseModel, StrictStr

from api.libs.exceptions import BadRequest
from api.libs.file import convert_halfwidth_to_fullwidth

from .file_extension import FileExtension


# ドキュメントの名前（拡張子なし）e.g. "sample"
class Name(BaseModel):
    value: StrictStr

    @classmethod
    def from_filename(cls, filename: str):
        try:
            name, _ = os.path.splitext(filename)
        except Exception:
            raise BadRequest("ファイル名が不正です。")
        if name == "":
            raise BadRequest("ファイル名が取得できません。")

        name = unicodedata.normalize("NFC", name)

        return cls(value=convert_halfwidth_to_fullwidth(name))

    def to_encoded_name(self):
        name_NFC = unicodedata.normalize("NFC", self.value)
        name_encoded = base64.urlsafe_b64encode(name_NFC.encode()).decode("utf-8")[:-2]
        return EncodedName(value=name_encoded)

    def to_encoded_name_v2(self):
        # TODO: 型を合わせるためだけにあるので、後で削除する
        encoded_name = self.value.replace("\\", "%5C")  # 九電のファイル名に含まれるバックスラッシュをエンコード
        return EncodedName(value=encoded_name)

    def to_blob_name(self, ext: FileExtension):
        encoded_name = self.to_encoded_name()
        return BlobName(value=f"{encoded_name.value}.{ext.value}")

    def to_pdf_blob_name(self):
        encoded_name = self.to_encoded_name()
        return BlobName(value=f"{encoded_name.value}.pdf")

    def to_blob_name_v2(self, ext: FileExtension):
        encoded_name = self.to_encoded_name_v2()
        return BlobName(value=f"{encoded_name.value}.{ext.value}")

    def to_pdf_blob_name_v2(self):
        encoded_name = self.to_encoded_name_v2()
        return BlobName(value=f"{encoded_name.value}.pdf")

    def to_displayable_blob_name(self, ext: FileExtension):
        return DisplayableBlobName(value=f"{self.value}.{ext.value}")


# Name をエンコードしたもの e.g. "c2FtcG"
class EncodedName(BaseModel):
    value: StrictStr


# Blob Storage に保存する際の名前 e.g. "c2FtcG.pdf"
class BlobName(BaseModel):
    value: StrictStr

    def file_extension(self):
        try:
            _, ext = os.path.splitext(self.value)
        except ValueError:
            raise BadRequest("ファイル名が不正です。")
        if ext == "":
            raise BadRequest("ファイル名が不正です。")
        return FileExtension(ext[1:].lower())

    def to_content_disposition(self):
        extension = self.file_extension().value
        blob_name = self.value.replace("%5C", "\\")  # 九電のファイル名に含まれるバックスラッシュをデコード

        file_name_to_content_disposition = {
            "pdf": "inline",
            "docx": "attachment;  filename={}".format(urllib.parse.quote(blob_name)),
            "xlsx": "attachment;  filename={}".format(urllib.parse.quote(blob_name)),
            "pptx": "attachment;  filename={}".format(urllib.parse.quote(blob_name)),
            "txt": "inline",
            "doc": "attachment;  filename={}".format(urllib.parse.quote(blob_name)),
            "xls": "attachment;  filename={}".format(urllib.parse.quote(blob_name)),
            "ppt": "attachment;  filename={}".format(urllib.parse.quote(blob_name)),
            "xlsm": "attachment;  filename={}".format(urllib.parse.quote(blob_name)),
            "xdw": "attachment;  filename={}".format(urllib.parse.quote(blob_name)),
        }
        content_disposition = file_name_to_content_disposition.get(extension, None)
        if content_disposition is None:
            raise BadRequest("ファイル形式が不正です。")

        return content_disposition


# ドキュメントの名前（拡張子あり）e.g. "sample.pdf"
class DisplayableBlobName(BlobName):
    def to_blob_name(self):
        try:
            name, ext = os.path.splitext(self.value)
        except ValueError:
            raise BadRequest("ファイル名が不正です。")
        if ext == "":
            raise BadRequest("ファイル名が不正です。")
        name = Name(value=name)
        encoded_name = name.to_encoded_name()
        return BlobName(value=f"{encoded_name.value}.{ext[1:].lower()}")

    def to_blob_name_v2(self):
        try:
            name, ext = os.path.splitext(self.value)
        except ValueError:
            raise BadRequest("ファイル名が不正です。")
        if ext == "":
            raise BadRequest("ファイル名が不正です。")
        name = Name(value=name)
        encoded_name = name.to_encoded_name_v2()
        return BlobName(value=f"{encoded_name.value}.{ext[1:].lower()}")

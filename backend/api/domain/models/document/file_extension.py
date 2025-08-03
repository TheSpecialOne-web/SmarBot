from enum import Enum
import os

from api.libs.exceptions import BadRequest


class FileExtension(str, Enum):
    PDF = "pdf"
    XLSX = "xlsx"
    DOCX = "docx"
    PPTX = "pptx"
    TXT = "txt"
    DOC = "doc"
    XLS = "xls"
    PPT = "ppt"
    XLSM = "xlsm"
    XDW = "xdw"

    @classmethod
    def from_filename(cls, filename: str, allow_legacy: bool) -> "FileExtension":
        try:
            _, ext = os.path.splitext(filename)
        except Exception:
            raise BadRequest("ファイル名が不正です。")
        if ext == "":
            raise BadRequest("ファイルの拡張子が取得できません。")
        ext_lower = ext[1:].lower()

        allowed_extensions = (
            [e.value for e in FileExtension] if allow_legacy else [e.value for e in FileExtension if not e.is_legacy()]
        )
        try:
            extension = cls(ext_lower)
        except Exception:
            raise BadRequest(
                f"ファイルの拡張子は {', '.join(allowed_extensions)} のいずれかである必要があります。",
            )

        if allow_legacy:
            return extension

        if extension.is_legacy():
            raise BadRequest(
                f"ファイルの拡張子は {', '.join(allowed_extensions)} のいずれかである必要があります。",
            )

        return extension

    def is_legacy(self) -> bool:
        return self in [
            FileExtension.DOC,
            FileExtension.PPT,
            FileExtension.XLSM,
            FileExtension.XDW,
        ]

    def to_content_type(self) -> str:
        return {
            FileExtension.PDF: "application/pdf",
            FileExtension.XLSX: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            FileExtension.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            FileExtension.PPTX: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            FileExtension.TXT: "text/plain; charset=utf-8",
            FileExtension.DOC: "application/msword",
            FileExtension.XLS: "application/vnd.ms-excel",
            FileExtension.PPT: "application/vnd.ms-powerpoint",
            FileExtension.XLSM: "application/vnd.ms-excel.sheet.macroenabled.12",
            FileExtension.XDW: "application/vnd.fujifilm.fb.docuworks",
        }[self]

    def is_indexing_supported(self) -> bool:
        """Function でのインデックスアップロードがサポートされているかどうかを返す。

        Returns:
            bool: サポートされている場合は True、それ以外の場合は False。
        """
        return self in [
            FileExtension.PDF,
            FileExtension.DOCX,
            FileExtension.XLSX,
            FileExtension.PPTX,
            FileExtension.TXT,
            FileExtension.XLS,
        ]

    def is_convertible_to_pdf(self) -> bool:
        """PDFへ変換されるべきファイルタイプかどうかを返す。

        Returns:
            bool: 変換されるべき場合は True、それ以外の場合は False。
        """
        return self in [
            FileExtension.DOCX,
            FileExtension.XLSX,
            FileExtension.PPTX,
        ]

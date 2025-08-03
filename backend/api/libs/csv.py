from io import StringIO
import os
from typing import Any, Optional

from fastapi import UploadFile
import pandas as pd

from api.libs.exceptions import BadRequest


def verify_csv_file_format(file: UploadFile) -> None:
    if not file or not file.filename:
        raise BadRequest("ファイルがアップロードされていません。")
    if not file.filename.endswith(".csv"):
        raise BadRequest("ファイルはcsv形式である必要があります。")
    try:
        _, ext = os.path.splitext(file.filename)
    except Exception:
        raise BadRequest("ファイルの拡張子が取得できません。")
    if ext != ".csv":
        raise BadRequest("ファイルはcsv形式である必要があります。")


ENCODING_TYPES = ["utf-8", "shift-jis", "cp932", "euc-jp"]


def get_decoded_csv_file(file: bytes) -> pd.DataFrame:
    csv_text = None
    for encoding_type in ENCODING_TYPES:
        try:
            csv_text = file.decode(encoding_type)
            break
        except UnicodeDecodeError:
            continue
    if csv_text is None:
        raise BadRequest("不正な文字コードです。")

    try:
        return pd.read_csv(StringIO(csv_text), dtype=str)
    except pd.errors.ParserError:
        raise BadRequest("csvファイルのデータ形式が正しくありません。")


def convert_dict_list_to_csv_string(data: list[dict], column_order: Optional[list[str]] = None) -> StringIO:
    csv = StringIO()
    df = pd.DataFrame(data)

    # カラムの順番を指定
    if column_order:
        df = df[column_order]

    # CSV Formula Injection対策
    def sanitize_formula(value: Any) -> Any:
        forbidden_chars = ("=", "+", "-", "@", " ", "\t", "\r", "\n", ";", "/", ",")
        if isinstance(value, str):
            if value.startswith(forbidden_chars):
                return f"'{value}"
        return value

    df = df.map(sanitize_formula)
    df.to_csv(csv, index=False)
    csv.seek(0)
    return csv


def convert_dict_list_to_csv_bytes(data: list[dict], column_order: Optional[list[str]] = None) -> bytes:
    csv = convert_dict_list_to_csv_string(data, column_order)
    return csv.getvalue().encode("utf-8")


def optimize_dict_list_for_excel(data: list[dict]) -> list[dict]:
    # Excel has a limit of 32767 characters and 253 new lines per cell
    EXCEL_MAX_WORDS = 30000
    EXCEL_MAX_NEW_LINES = 250

    for i, row in enumerate(data):
        new_rows_for_exceeding_words = []
        for key, value in row.items():
            if not isinstance(value, str):
                continue

            # replace new lines with spaces if the number of new lines exceeds the limit
            if value.count("\n") > EXCEL_MAX_NEW_LINES:
                value = value.replace("\n", " ")

            # split the value into multiple rows if the number of characters exceeds the limit
            row[key] = value[:EXCEL_MAX_WORDS]
            remaining_value = value[EXCEL_MAX_WORDS:]
            while len(remaining_value) > 0:
                new_row = {k: "" for k in row.keys()}
                new_row[key] = remaining_value[:EXCEL_MAX_WORDS]
                remaining_value = remaining_value[EXCEL_MAX_WORDS:]
                new_rows_for_exceeding_words.append(new_row)
        data[i + 1 : i + 1] = new_rows_for_exceeding_words
    return data

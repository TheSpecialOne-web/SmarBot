from datetime import datetime, timedelta


def convert_utc_to_jst(utc_datetime: datetime) -> datetime:
    return utc_datetime + timedelta(hours=9)


def convert_jst_to_utc(jst_datetime: datetime) -> datetime:
    return jst_datetime - timedelta(hours=9)

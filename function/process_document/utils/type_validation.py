from typing import Any


def validate_int(int_like: Any) -> int | None:
    if int_like is None:
        return None
    try:
        return int(int_like)
    except Exception:
        return None

from typing import Any

from pydantic import BaseModel


class Chunk(BaseModel):
    value: dict[str, Any]


class ChunksForCreate(BaseModel):
    chunks: list[Chunk]

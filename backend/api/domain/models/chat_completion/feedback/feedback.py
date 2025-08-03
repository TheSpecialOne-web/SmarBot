from typing import Optional

from pydantic import BaseModel

from .comment import Comment
from .evaluation import Evaluation


class Feedback(BaseModel):
    evaluation: Optional[Evaluation] = None
    comment: Optional[Comment] = None

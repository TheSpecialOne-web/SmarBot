from pydantic import BaseModel

from ..bot.id import Id as BotId
from .action import Action


class Policy(BaseModel):
    bot_id: BotId
    action: Action

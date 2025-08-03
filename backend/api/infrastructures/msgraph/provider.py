from injector import Module, provider

from api.domain.services.msgraph import IMsgraphService

from .msgraph import MsgraphService


class MsgraphModule(Module):
    @provider
    def msgraph_service(self) -> IMsgraphService:
        return MsgraphService()

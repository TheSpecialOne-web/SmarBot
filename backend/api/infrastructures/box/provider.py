from injector import Module, provider

from api.domain.services.box import IBoxService

from .box import BoxService


class BoxModule(Module):
    @provider
    def box_service(self) -> IBoxService:
        return BoxService()

from injector import Module, provider

from api.domain.services.metabase import IMetabaseService

from .metabase import MetabaseService


class MetabaseModule(Module):
    @provider
    def metabase_service(self) -> IMetabaseService:
        return MetabaseService()

from injector import Module, provider

from api.domain.services.bing_search import IBingSearchService

from .bing_search import BingSearchService


class BingSearchModule(Module):
    @provider
    def bing_search_service(self) -> IBingSearchService:
        return BingSearchService()

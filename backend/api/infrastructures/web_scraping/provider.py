from injector import Module, provider

from api.domain.services.web_scraping import IWebScrapingService

from .web_scraping import WebScrapingService


class WebScrapingModule(Module):
    @provider
    def web_scraping_service(self) -> IWebScrapingService:
        return WebScrapingService()

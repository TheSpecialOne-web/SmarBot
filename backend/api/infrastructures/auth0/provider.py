from injector import Module, provider

from api.domain.services.auth0 import IAuth0Service

from .auth0 import Auth0Service


class Auth0Module(Module):
    @provider
    def auth0_service(self) -> IAuth0Service:
        return Auth0Service()

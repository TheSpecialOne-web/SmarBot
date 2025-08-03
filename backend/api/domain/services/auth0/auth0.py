from abc import ABC, abstractmethod

from ...models.user import Email, ExternalUserId, IdpUser


class IAuth0Service(ABC):
    @abstractmethod
    def validate_token(self, token: str) -> ExternalUserId:
        pass

    @abstractmethod
    def find_by_id(self, id: ExternalUserId) -> IdpUser:
        pass

    @abstractmethod
    def find_by_emails(self, emails: list[Email]) -> list[IdpUser]:
        pass

    @abstractmethod
    def create_user(self, email: Email) -> str:
        pass

    @abstractmethod
    def delete_user(self, email: Email) -> None:
        pass

    @abstractmethod
    def delete_users(self, emails: list[Email]) -> None:
        pass

    @abstractmethod
    def bulk_create_auth0_users(self, emails: list[Email]) -> list[IdpUser]:
        pass

from abc import ABC, abstractmethod

from injector import inject

from api.domain.models.notification import (
    Id,
    INotificationRepository,
    Notification,
    NotificationForCreate,
    NotificationForUpdate,
)
from api.domain.models.user import Role
from api.libs.exceptions import BadRequest


class INotificationUseCase(ABC):
    @abstractmethod
    def find_all_notifications(self) -> list[Notification]:
        pass

    @abstractmethod
    def find_notifications_by_roles(self, roles: list[Role]) -> list[Notification]:
        pass

    @abstractmethod
    def create_notification(self, notification: NotificationForCreate) -> None:
        pass

    @abstractmethod
    def update_notification(self, notification: NotificationForUpdate) -> None:
        pass

    @abstractmethod
    def archive_notification(self, id: Id) -> None:
        pass


class NotificationUseCase(INotificationUseCase):
    @inject
    def __init__(self, notification_repo: INotificationRepository):
        self.notification_repo = notification_repo

    def find_all_notifications(self) -> list[Notification]:
        return self.notification_repo.find_all()

    def find_notifications_by_roles(self, roles: list[Role]) -> list[Notification]:
        if Role.ADMIN in roles:
            return self.notification_repo.find_admin_notifications()
        return self.notification_repo.find_user_notifications()

    def create_notification(self, notification: NotificationForCreate) -> None:
        return self.notification_repo.create(notification)

    def update_notification(self, notification_for_update: NotificationForUpdate) -> None:
        notification = self.notification_repo.find_by_id(notification_for_update.id)
        if notification.is_archived.root:
            raise BadRequest("通知はアーカイブされています。")
        notification.update(notification_for_update)
        return self.notification_repo.update(notification)

    def archive_notification(self, id: Id) -> None:
        notification = self.notification_repo.find_by_id(id)
        if notification.is_archived.root:
            raise BadRequest("通知はアーカイブされています。")
        notification.archive()
        return self.notification_repo.update(notification)

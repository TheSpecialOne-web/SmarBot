from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from api.domain.models.notification import (
    Id,
    INotificationRepository,
    Notification,
    NotificationForCreate,
    RecipientType,
)
from api.libs.exceptions import NotFound

from .models.notification import Notification as NotificationModel


class NotificationRepository(INotificationRepository):
    def __init__(self, session: Session):
        self.session = session

    def find_all(self) -> list[Notification]:
        notifications = self.session.execute(select(NotificationModel)).scalars().all()
        return [notification.to_domain() for notification in notifications]

    def find_by_id(self, notification_id: Id) -> Notification:
        notification = self.session.execute(
            select(NotificationModel).where(NotificationModel.id == notification_id.root)
        ).scalar_one_or_none()
        if notification is None:
            raise NotFound("通知が見つかりませんでした。")
        return notification.to_domain()

    def find_user_notifications(self) -> list[Notification]:
        now = datetime.now()
        today = datetime(now.year, now.month, now.day, 0, 0, 0)
        notifications = (
            self.session.execute(
                select(NotificationModel)
                .where(NotificationModel.recipient_type == RecipientType.USER.value)
                .where(NotificationModel.is_archived.is_(False))
                .where(NotificationModel.start_date <= today)
                .where(NotificationModel.end_date >= today)
                .order_by(NotificationModel.start_date.desc())
            )
            .scalars()
            .all()
        )
        return [notification.to_domain() for notification in notifications]

    def find_admin_notifications(self) -> list[Notification]:
        now = datetime.now()
        today = datetime(now.year, now.month, now.day, 0, 0, 0)

        notifications = (
            self.session.execute(
                select(NotificationModel)
                .where(NotificationModel.start_date <= today)
                .where(NotificationModel.end_date >= today)
                .where(NotificationModel.is_archived.is_(False))
                .order_by(NotificationModel.start_date.desc())
            )
            .scalars()
            .all()
        )
        return [notification.to_domain() for notification in notifications]

    def create(self, notification: NotificationForCreate) -> None:
        try:
            new_notification = NotificationModel.from_domain(domain_model=notification)
            self.session.add(new_notification)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

    def update(self, notification: Notification) -> None:
        try:
            self.session.execute(
                update(NotificationModel)
                .where(NotificationModel.id == notification.id.root)
                .values(
                    title=notification.title.root,
                    content=notification.content.root,
                    end_date=notification.end_date.root,
                    recipient_type=notification.recipient_type.value,
                    is_archived=notification.is_archived.root,
                )
            )
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

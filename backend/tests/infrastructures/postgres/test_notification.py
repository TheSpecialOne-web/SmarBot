from datetime import datetime, timedelta

from sqlalchemy import select

from api.database import SessionFactory
from api.domain.models import notification as notification_domain
from api.infrastructures.postgres.models.notification import Notification
from api.infrastructures.postgres.notification import NotificationRepository


class TestNotificationRepository:
    def setup_method(self):
        self.session = SessionFactory()
        self.notification_repo = NotificationRepository(self.session)

    def teardown_method(self):
        self.session.close()

    def test_find_all(self, notifications_seed: list[notification_domain.Notification]):
        notifications = self.notification_repo.find_all()
        assert notifications == notifications_seed

    def test_find_user_notifications(self, notifications_seed: list[notification_domain.Notification]):
        user_notifications = list(
            filter(
                lambda notification: notification.recipient_type.value == notification_domain.RecipientType.USER,
                notifications_seed,
            )
        )
        notifications = self.notification_repo.find_user_notifications()
        assert notifications == user_notifications

    def test_find_admin_notifications(self, notifications_seed: list[notification_domain.Notification]):
        notifications = self.notification_repo.find_admin_notifications()
        assert notifications == notifications_seed

    def test_find_by_id(self, notifications_seed: list[notification_domain.Notification]):
        notification = notifications_seed[0]
        found_notification = self.notification_repo.find_by_id(notification.id)
        assert found_notification is not None
        assert found_notification == notification

    def test_create(self):
        notification_for_create = notification_domain.NotificationForCreate(
            title=notification_domain.Title(root="test"),
            content=notification_domain.Content(root="test"),
            recipient_type=notification_domain.RecipientType(notification_domain.RecipientType.USER),
            start_date=notification_domain.StartDate(root=datetime.now()),
            end_date=notification_domain.EndDate(root=datetime.now() + timedelta(days=1)),
        )

        self.notification_repo.create(notification_for_create)
        created_notification = (
            self.session.execute(select(Notification).where(Notification.id == notification_for_create.id.root))
            .scalars()
            .first()
        )
        assert created_notification is not None
        assert created_notification.title == notification_for_create.title.root
        assert created_notification.content == notification_for_create.content.root
        assert created_notification.recipient_type == notification_for_create.recipient_type.value
        assert created_notification.start_date == notification_for_create.start_date.root
        assert created_notification.end_date == notification_for_create.end_date.root

    def test_update(self, notifications_seed: list[notification_domain.Notification]):
        notification = notifications_seed[0]
        notification_for_update = notification_domain.Notification(
            id=notification.id,
            title=notification_domain.Title(root="updated"),
            content=notification_domain.Content(root="updated"),
            recipient_type=notification_domain.RecipientType(notification_domain.RecipientType.USER),
            start_date=notification_domain.StartDate(root=notification.start_date.root),
            end_date=notification_domain.EndDate(root=notification.end_date.root),
            is_archived=notification_domain.IsArchived(root=notification.is_archived.root),
        )

        self.notification_repo.update(notification_for_update)
        updated_notification = (
            self.session.execute(select(Notification).where(Notification.id == notification.id.root)).scalars().first()
        )
        assert updated_notification is not None
        assert updated_notification.title == notification_for_update.title.root
        assert updated_notification.content == notification_for_update.content.root
        assert updated_notification.recipient_type == notification_for_update.recipient_type.value
        assert updated_notification.end_date == notification_for_update.end_date.root
        assert updated_notification.is_archived == notification_for_update.is_archived.root

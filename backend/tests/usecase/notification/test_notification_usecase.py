from datetime import datetime, timedelta
from unittest.mock import Mock
from uuid import uuid4

import pytest

from api.domain.models import notification as notification_domain
from api.domain.models.user import Role
from api.usecase.notification.notification import NotificationUseCase


class TestNotificationUseCase:
    @pytest.fixture
    def setup(self):
        self.notification_repo = Mock()
        self.notification_usecase = NotificationUseCase(
            notification_repo=self.notification_repo,
        )

    def test_find_all_notifications(self, setup):
        want = [
            notification_domain.Notification(
                id=notification_domain.Id(root=uuid4()),
                title=notification_domain.Title(root="test"),
                content=notification_domain.Content(root="test"),
                recipient_type=notification_domain.RecipientType(notification_domain.RecipientType.USER),
                start_date=notification_domain.StartDate(root=datetime.now()),
                end_date=notification_domain.EndDate(root=datetime.now()),
                is_archived=notification_domain.IsArchived(root=False),
            ),
            notification_domain.Notification(
                id=notification_domain.Id(root=uuid4()),
                title=notification_domain.Title(root="test"),
                content=notification_domain.Content(root="test"),
                recipient_type=notification_domain.RecipientType(notification_domain.RecipientType.USER),
                start_date=notification_domain.StartDate(root=datetime.now()),
                end_date=notification_domain.EndDate(root=datetime.now()),
                is_archived=notification_domain.IsArchived(root=False),
            ),
        ]
        self.notification_usecase.notification_repo.find_all.return_value = want
        notifications = self.notification_usecase.find_all_notifications()
        self.notification_usecase.notification_repo.find_all.assert_called_once()
        assert notifications == want

    def test_find_notifications_by_roles_user(self, setup):
        want = [
            notification_domain.Notification(
                id=notification_domain.Id(root=uuid4()),
                title=notification_domain.Title(root="test"),
                content=notification_domain.Content(root="test"),
                recipient_type=notification_domain.RecipientType(notification_domain.RecipientType.USER),
                start_date=notification_domain.StartDate(root=datetime.now()),
                end_date=notification_domain.EndDate(root=datetime.now()),
                is_archived=notification_domain.IsArchived(root=False),
            ),
        ]
        self.notification_usecase.notification_repo.find_user_notifications.return_value = want
        notifications = self.notification_usecase.find_notifications_by_roles(roles=[Role(Role.USER)])
        self.notification_usecase.notification_repo.find_user_notifications.assert_called_once()
        assert notifications == want

    def test_find_notifications_by_roles_admin(self, setup):
        want = [
            notification_domain.Notification(
                id=notification_domain.Id(root=uuid4()),
                title=notification_domain.Title(root="test"),
                content=notification_domain.Content(root="test"),
                recipient_type=notification_domain.RecipientType(notification_domain.RecipientType.USER),
                start_date=notification_domain.StartDate(root=datetime.now()),
                end_date=notification_domain.EndDate(root=datetime.now()),
                is_archived=notification_domain.IsArchived(root=False),
            ),
            notification_domain.Notification(
                id=notification_domain.Id(root=uuid4()),
                title=notification_domain.Title(root="test"),
                content=notification_domain.Content(root="test"),
                recipient_type=notification_domain.RecipientType(notification_domain.RecipientType.ADMIN),
                start_date=notification_domain.StartDate(root=datetime.now()),
                end_date=notification_domain.EndDate(root=datetime.now()),
                is_archived=notification_domain.IsArchived(root=False),
            ),
        ]
        self.notification_usecase.notification_repo.find_admin_notifications.return_value = want
        notifications = self.notification_usecase.find_notifications_by_roles(roles=[Role(Role.ADMIN)])
        self.notification_usecase.notification_repo.find_admin_notifications.assert_called_once()
        assert notifications == want

    def test_create_notification(self, setup):
        notification_for_create = notification_domain.NotificationForCreate(
            title=notification_domain.Title(root="test"),
            content=notification_domain.Content(root="test"),
            recipient_type=notification_domain.RecipientType(notification_domain.RecipientType.USER),
            start_date=notification_domain.StartDate(root=datetime.now()),
            end_date=notification_domain.EndDate(root=datetime.now() + timedelta(days=1)),
        )
        self.notification_usecase.notification_repo.create.return_value = None
        self.notification_usecase.create_notification(notification_for_create)
        self.notification_repo.create.assert_called_once_with(notification_for_create)

    def test_update_notification(self, setup):
        notification_for_update = notification_domain.NotificationForUpdate(
            id=notification_domain.Id(root=uuid4()),
            title=notification_domain.Title(root="updated"),
            content=notification_domain.Content(root="updated"),
            recipient_type=notification_domain.RecipientType(notification_domain.RecipientType.USER),
            end_date=notification_domain.EndDate(root=datetime.now() + timedelta(days=1)),
        )

        notification = notification_domain.Notification(
            id=notification_for_update.id,
            title=notification_domain.Title(root="test"),
            content=notification_domain.Content(root="test"),
            recipient_type=notification_domain.RecipientType(notification_domain.RecipientType.USER),
            start_date=notification_domain.StartDate(root=datetime.now()),
            end_date=notification_domain.EndDate(root=datetime.now()),
            is_archived=notification_domain.IsArchived(root=False),
        )

        self.notification_usecase.notification_repo.find_by_id.return_value = notification
        self.notification_usecase.notification_repo.update.return_value = None
        notification.update(notification_for_update)
        self.notification_usecase.update_notification(notification_for_update)
        self.notification_usecase.notification_repo.update.assert_called_once_with(notification)

    def test_archive_notification(self, setup):
        notification = notification_domain.Notification(
            id=notification_domain.Id(root=uuid4()),
            title=notification_domain.Title(root="test"),
            content=notification_domain.Content(root="test"),
            recipient_type=notification_domain.RecipientType(notification_domain.RecipientType.USER),
            start_date=notification_domain.StartDate(root=datetime.now()),
            end_date=notification_domain.EndDate(root=datetime.now()),
            is_archived=notification_domain.IsArchived(root=False),
        )
        self.notification_usecase.notification_repo.find_by_id.return_value = notification
        self.notification_usecase.notification_repo.update.return_value = None
        self.notification_usecase.archive_notification(notification.id)
        self.notification_usecase.notification_repo.find_by_id.assert_called_once_with(notification.id)
        self.notification_usecase.notification_repo.update.assert_called_once_with(notification)

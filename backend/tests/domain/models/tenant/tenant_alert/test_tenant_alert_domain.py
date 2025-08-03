from datetime import datetime

from api.domain.models.search import StorageUsage
from api.domain.models.tenant import Id as TenantId
from api.domain.models.tenant.tenant_alert import Alert, AlertType, Limit, TenantAlert
from api.domain.models.token import TokenCount


class TestAlert:
    def test_to_usage_rate(self):
        test_cases = [
            {"alert": Alert(usage=TokenCount(root=79.9), limit=Limit(root=100), type=AlertType.TOKEN), "expected": 70},
            {"alert": Alert(usage=TokenCount(root=80), limit=Limit(root=100), type=AlertType.TOKEN), "expected": 80},
            {"alert": Alert(usage=TokenCount(root=100), limit=Limit(root=100), type=AlertType.TOKEN), "expected": 100},
            {
                "alert": Alert(usage=StorageUsage(root=120), limit=Limit(root=100), type=AlertType.STORAGE),
                "expected": 100,
            },
            {"alert": Alert(usage=StorageUsage(root=120), limit=Limit(root=0), type=AlertType.STORAGE), "expected": 0},
        ]
        for case in test_cases:
            alert: Alert = case["alert"]
            assert alert.to_usage_rate() == case["expected"]

    def test_should_send_alert(self):
        test_cases = [
            # 閾値のテスト
            {
                "alert": Alert(usage=TokenCount(root=79.9), limit=Limit(root=100), type=AlertType.TOKEN),
                "last_alerted_at_jst": None,
                "last_alerted_threshold": None,
                "expected": False,
            },
            {
                "alert": Alert(usage=TokenCount(root=80), limit=Limit(root=100), type=AlertType.TOKEN),
                "last_alerted_at_jst": None,
                "last_alerted_threshold": None,
                "expected": True,
            },
            {
                "alert": Alert(usage=TokenCount(root=100), limit=Limit(root=100), type=AlertType.TOKEN),
                "last_alerted_at_jst": None,
                "last_alerted_threshold": None,
                "expected": True,
            },
            {
                "alert": Alert(usage=StorageUsage(root=120), limit=Limit(root=100), type=AlertType.STORAGE),
                "last_alerted_at_jst": None,
                "last_alerted_threshold": None,
                "expected": True,
            },
            # limit = 0 の時のテスト
            {
                "alert": Alert(usage=StorageUsage(root=120), limit=Limit(root=0), type=AlertType.STORAGE),
                "last_alerted_at_jst": None,
                "last_alerted_threshold": None,
                "expected": False,
            },
            # 月に通知した時の閾値のテスト
            {
                "alert": Alert(usage=TokenCount(root=80), limit=Limit(root=100), type=AlertType.TOKEN),
                "last_alerted_at_jst": datetime.now(),
                "last_alerted_threshold": 80,
                "expected": False,
            },
            {
                "alert": Alert(usage=TokenCount(root=89.9), limit=Limit(root=100), type=AlertType.TOKEN),
                "last_alerted_at_jst": datetime.now(),
                "last_alerted_threshold": 80,
                "expected": False,
            },
            {
                "alert": Alert(usage=TokenCount(root=90), limit=Limit(root=100), type=AlertType.TOKEN),
                "last_alerted_at_jst": datetime.now(),
                "last_alerted_threshold": 80,
                "expected": True,
            },
            {
                "alert": Alert(usage=TokenCount(root=120), limit=Limit(root=100), type=AlertType.TOKEN),
                "last_alerted_at_jst": datetime.now(),
                "last_alerted_threshold": 90,
                "expected": True,
            },
            {
                "alert": Alert(usage=TokenCount(root=130), limit=Limit(root=100), type=AlertType.TOKEN),
                "last_alerted_at_jst": datetime.now(),
                "last_alerted_threshold": 100,
                "expected": False,
            },
        ]
        for case in test_cases:
            alert: Alert = case["alert"]
            last_alerted_at_jst = case["last_alerted_at_jst"]
            last_alerted_threshold = case["last_alerted_threshold"]
            assert alert.should_send_alert(last_alerted_at_jst, last_alerted_threshold) == case["expected"]


class TestTenantAlert:
    def test_update_by_alerts(self):
        # Input
        tenant_alert = TenantAlert(tenant_id=TenantId(value=1))
        token_alert = Alert(usage=TokenCount(root=95), limit=Limit(root=100), type=AlertType.TOKEN)
        storage_alert = Alert(usage=StorageUsage(root=120), limit=Limit(root=100), type=AlertType.STORAGE)
        alerts = [token_alert, storage_alert]
        now = datetime.now()

        # Execute
        tenant_alert.update_by_alerts(alerts, now)

        # Assert
        assert tenant_alert.last_token_alerted_at is not None
        assert tenant_alert.last_token_alerted_at.root == now
        assert tenant_alert.last_token_alerted_threshold is not None
        assert tenant_alert.last_token_alerted_threshold.root == token_alert.to_usage_rate()
        assert tenant_alert.last_storage_alerted_at is not None
        assert tenant_alert.last_storage_alerted_at.root == now
        assert tenant_alert.last_storage_alerted_threshold is not None
        assert tenant_alert.last_storage_alerted_threshold.root == storage_alert.to_usage_rate()

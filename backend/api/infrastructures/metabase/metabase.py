import os
import time

import jwt

from api.domain.models.tenant.id import Id as TenantId
from api.domain.services.metabase.metabase import IMetabaseService

METABASE_SITE_URL = os.environ.get("METABASE_SITE_URL")
METABASE_SECRET_KEY = os.environ.get("METABASE_SECRET_KEY")
TENANT_DAILY_USAGE_DASHBOARD_ID = os.environ.get("TENANT_DAILY_USAGE_DASHBOARD_ID")
TENANT_MONTHLY_USAGE_DASHBOARD_ID = os.environ.get("TENANT_MONTHLY_USAGE_DASHBOARD_ID")


class MetabaseService(IMetabaseService):
    def find_tenant_usage_dashboard(self, tenant_id: TenantId, year_month: str, type: str) -> str:
        if METABASE_SITE_URL is None:
            raise Exception("METABASE_SITE_URL is not set")
        if METABASE_SECRET_KEY is None:
            raise Exception("METABASE_SECRET_KEY is not set")
        if TENANT_DAILY_USAGE_DASHBOARD_ID is None:
            raise Exception("TENANT_DAILY_USAGE_DASHBOARD_ID is not set")
        if TENANT_MONTHLY_USAGE_DASHBOARD_ID is None:
            raise Exception("TENANT_MONTHLY_USAGE_DASHBOARD_ID is not set")

        if type == "day":
            payload = {
                "resource": {"dashboard": int(TENANT_DAILY_USAGE_DASHBOARD_ID)},
                "params": {
                    "tenant_id": [tenant_id.value],
                    "year_month": year_month,
                },
                "exp": round(time.time()) + (5 * 60),
            }
            token = jwt.encode(payload, METABASE_SECRET_KEY, algorithm="HS256")

            return f"{METABASE_SITE_URL}/embed/dashboard/{token}#bordered=true&titled=false"
        if type == "month":
            payload = {
                "resource": {"dashboard": int(TENANT_MONTHLY_USAGE_DASHBOARD_ID)},
                "params": {"tenant_id": [tenant_id.value], "year_month": "past12months"},
                "exp": round(time.time()) + (5 * 60),
            }
            token = jwt.encode(payload, METABASE_SECRET_KEY, algorithm="HS256")

            return f"{METABASE_SITE_URL}/embed/dashboard/{token}#bordered=true&titled=false"

        raise Exception("type must be day or month")

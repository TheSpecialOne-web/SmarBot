from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from api.libs.ctx import get_user_from_request
from api.libs.feature_flag import get_feature_flag


class MaintenanceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)
        if request.url.path == "/backend-api/userinfo":
            return await call_next(request)

        tenant = get_user_from_request(request).tenant

        MAINTENANCE_MODE = "maintenance-mode"
        # LaunchDarklyからメンテナンスフラグの状態を取得
        flag = get_feature_flag(MAINTENANCE_MODE, tenant.id, tenant.name)

        # メンテナンスモードが有効の場合、アクセスを遮断
        if flag:
            return JSONResponse(
                content={"error": "メンテナンス中です。しばらくしてから再度お試しください。"}, status_code=503
            )
        return await call_next(request)

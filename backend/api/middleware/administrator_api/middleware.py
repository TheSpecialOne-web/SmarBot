from fastapi import Request, Response
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from api.database import get_db_session_from_request
from api.infrastructures.auth0.auth0 import Auth0Service
from api.infrastructures.postgres.user import UserRepository
from api.libs.api_log import log_api_access
from api.libs.error_handlers import ErrorHandlers
from api.libs.exceptions import Forbidden, NotFound, Unauthorized
from api.libs.logging import get_logger

logger = get_logger()
auth0_service = Auth0Service()
security = HTTPBearer()


class ValidateAdministratorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)

        try:
            token = await security(request)
            if token is None:
                raise Unauthorized("認証情報がありません")

            external_user_id = auth0_service.validate_token(token.credentials)

            session = get_db_session_from_request(request)
            user_repo = UserRepository(session)
            user = None
            if external_user_id.is_email_connection():
                user = user_repo.get_user_info_by_external_id(external_user_id)
            elif external_user_id.is_entra_id():
                idp_user = auth0_service.find_by_id(external_user_id)
                user = user_repo.get_user_info_by_email(idp_user.email)

            if user is None:
                raise NotFound("ユーザーが見つかりませんでした")

            if not user.is_administrator.value:
                raise Forbidden("運営者権限が必要です")

            log_api_access(request=request, logger=logger, user_id=user.id, tenant_id=None)

            return await call_next(request)
        except Exception as e:
            return ErrorHandlers().handle_error(request, e)

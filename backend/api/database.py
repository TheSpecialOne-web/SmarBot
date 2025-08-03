import os

from azure.identity import DefaultAzureCredential
from fastapi import Request, Response
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from api.libs.app_env import app_env
from api.libs.retry import retry_azure_auth_error

GET_DB_TOKEN_URL = "https://ossrdbms-aad.database.windows.net/.default"
db_host = os.environ.get("DB_HOST", "")
db_name = os.environ.get("DB_NAME", "")
db_user = os.environ.get("DB_USER", "")


@retry_azure_auth_error
def get_database_uri() -> str:
    if app_env.is_localhost():
        password = os.environ.get("DB_PASSWORD")
        return f"postgresql://{db_user}:{password}@{db_host}/{db_name}?client_encoding=utf8"

    azure_credential = DefaultAzureCredential()
    token = azure_credential.get_token(GET_DB_TOKEN_URL).token
    return f"postgresql://{db_user}:{token}@{db_host}:5432/{db_name}?client_encoding=utf8"


# Creating DB engine
engine = create_engine(get_database_uri(), pool_size=20, max_overflow=10, pool_recycle=3600)

# Creating and Managing session.
SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def set_db_session_to_request(request: Request, session: Session):
    request.state.__setattr__("session", session)


def get_db_session_from_request(request: Request) -> Session:
    session = getattr(request.state, "session", None)
    if session is None:
        raise ValueError("Session is not set to request")
    if not isinstance(session, Session):
        raise ValueError("Session is not an instance of Session")
    return session


def remove_db_session_from_request(request: Request):
    if not hasattr(request.state, "session"):
        print("Session is not set to request")
        return
    request.state.__delattr__("session")


class DBSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        session = SessionFactory()
        try:
            set_db_session_to_request(request, session)
            return await call_next(request)
        finally:
            session.close()
            remove_db_session_from_request(request)

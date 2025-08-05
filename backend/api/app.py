from dotenv import load_dotenv

# 一番最初に読み込む
env_path = ".env"
load_dotenv(env_path)

import os

from azure.monitor.opentelemetry import configure_azure_monitor

from api.libs.logging import LOGGER_NAME

APP_ENV = os.environ.get("APP_ENV", "localhost")
APP_URL = os.environ.get("APP_URL")

# NOTE: Initialize the Azure Monitor SDK before your app has been initialized
if APP_ENV != "localhost":
    configure_azure_monitor(
        logger_name=LOGGER_NAME,
    )

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from opentelemetry import trace  # NOQA
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

from api.controllers.administrator_api.router import administrator_api_router
from api.controllers.api.router import external_api_router
from api.controllers.backend_api.router import backend_api_router
from api.controllers.automotive.router import automotive_router
from api.database import DBSessionMiddleware
from api.libs.ctx import set_trace_id_to_request
from api.libs.error_handlers import http_exception_handler, request_validation_exception_handler
from api.libs.sentry import init_sentry
from api.middleware.administrator_api.middleware import ValidateAdministratorMiddleware
from api.middleware.backend_api.maintenance_middleware import MaintenanceMiddleware
from api.middleware.backend_api.middleware import ValidateTokenMiddleware

init_sentry()

app = FastAPI()
app.add_middleware(DBSessionMiddleware)


@app.middleware("http")
async def set_trace_id(request: Request, call_next):
    set_trace_id_to_request(request)
    return await call_next(request)


external_api = FastAPI(title="api")
external_api.add_exception_handler(StarletteHTTPException, http_exception_handler)
external_api.add_exception_handler(RequestValidationError, request_validation_exception_handler)
external_api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
external_api.include_router(external_api_router)
external_api.include_router(automotive_router)

backend_api = FastAPI(title="backend_api")
backend_api.add_exception_handler(StarletteHTTPException, http_exception_handler)
backend_api.add_exception_handler(RequestValidationError, request_validation_exception_handler)

# ミドルウェアは後に追加したものが先に実行される
backend_api.add_middleware(MaintenanceMiddleware)
backend_api.add_middleware(ValidateTokenMiddleware)
backend_api.add_middleware(
    CORSMiddleware,
    allow_origins=[APP_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
backend_api.include_router(backend_api_router)


administrator_api = FastAPI(title="administrator_api")
administrator_api.add_exception_handler(StarletteHTTPException, http_exception_handler)
administrator_api.add_exception_handler(RequestValidationError, request_validation_exception_handler)
administrator_api.add_middleware(ValidateAdministratorMiddleware)
administrator_api.add_middleware(
    CORSMiddleware,
    allow_origins=[APP_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
administrator_api.include_router(administrator_api_router)


@app.get("/health", status_code=200)
def healthcheck():
    return {"status": "OK"}


app.mount("/api", external_api)
app.mount("/backend-api", backend_api)
app.mount("/administrator-api", administrator_api)

from uuid import UUID

from anthropic import APIStatusError
from fastapi import Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from api.libs.ctx import get_trace_id_from_request
from api.libs.exceptions import HTTPException
from api.libs.logging import StructLogger, get_logger


class ErrorHandlers:
    logger: StructLogger

    def __init__(self):
        self.logger = get_logger()

    def _create_message(self, code: int, message: str, trace_id: UUID):
        return {
            "code": code,
            "message": message,
            "trace_id": str(trace_id),
        }

    # 400番台
    def handle_client_error(self, e: HTTPException, trace_id: UUID):
        msg = self._create_message(e.status_code, e.detail, trace_id)
        self.logger.warning(msg, exc_info=e)
        return JSONResponse(status_code=e.status_code, content={"error": e.detail or ""})

    # 500
    def handle_internal_error(self, e: Exception, trace_id: UUID):
        msg = self._create_message(500, str(e), trace_id)
        self.logger.error(msg, exc_info=e)
        return JSONResponse(status_code=500, content={"error": ""})

    def handle_error(self, reqeust: Request, e: Exception):
        trace_id = get_trace_id_from_request(reqeust)
        if isinstance(e, ValidationError):
            return self.handle_validation_error(e, trace_id)
        # 400番台
        if isinstance(e, HTTPException) and e.status_code >= 400 and e.status_code < 500:
            return self.handle_client_error(e, trace_id)
        # 500
        return self.handle_internal_error(e, trace_id)

    # validation error
    def handle_validation_error(self, e: ValidationError, trace_id: UUID):
        msg = self._create_message(400, str(e), trace_id)
        self.logger.warning(msg, exc_info=e)
        return JSONResponse(
            status_code=400,
            content={
                "error": "validation error",
                "details": [{"loc": error["loc"], "msg": error["msg"], "type": error["type"]} for error in e.errors()],
            },
        )

    def handle_request_validation_error(self, request: Request, e: RequestValidationError):
        trace_id = get_trace_id_from_request(request)
        msg = self._create_message(422, str(e), trace_id)
        self.logger.warning(msg, exc_info=e)
        return JSONResponse(
            status_code=422,
            content={"error": "validation error", "details": jsonable_encoder(e.errors())},
        )

    # Anthropic error
    def handle_over_loaded_error(self, e: APIStatusError, trace_id: UUID):
        msg = self._create_message(e.status_code, e.message, trace_id)
        self.logger.warning(msg, exc_info=e)
        return JSONResponse(status_code=500, content={"error": ""})


def http_exception_handler(request: Request, exc: Exception) -> Response:
    return ErrorHandlers().handle_error(request, exc)


def request_validation_exception_handler(request: Request, exc: Exception) -> Response:
    if isinstance(exc, RequestValidationError):
        return ErrorHandlers().handle_request_validation_error(request, exc)
    return ErrorHandlers().handle_error(request, exc)

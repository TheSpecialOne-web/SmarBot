import json
import logging
import os
import sys
import time
from typing import TYPE_CHECKING, Any, MutableMapping

from opencensus.ext.azure.log_exporter import AzureLogHandler

if TYPE_CHECKING:
    _LoggerAdapter = logging.LoggerAdapter[logging.Logger]
else:
    _LoggerAdapter = logging.LoggerAdapter

app_env = os.environ.get("APP_ENV", "localhost")
is_local = app_env == "localhost"

AZURE_APPINSIGHTS_CONNECTION_STRING = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")


def get_logger(name) -> "StructLogger":
    handlers = []
    # For Application Insights
    if not is_local and AZURE_APPINSIGHTS_CONNECTION_STRING is not None:
        azure_log_handler = AzureLogHandler(connection_string=AZURE_APPINSIGHTS_CONNECTION_STRING)
        azure_log_handler.formatter = StructuralFormatter()
        handlers.append(azure_log_handler)
    # For stdout
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.formatter = StructuralFormatter()
    handlers.append(stream_handler)
    # Set logger
    logging.basicConfig(handlers=handlers, level=logging.INFO)
    logger = StructLogger(logging.getLogger(name), {})
    return logger


class StructLogger(_LoggerAdapter):
    def process(self, msg: str, kwargs: MutableMapping[str, Any]) -> tuple[str, dict[str, Any]]:
        information = {
            "extra": {
                "kwargs": kwargs,
                "structual": True,
            },
            "stack_info": kwargs.pop("stack_info", False),
            "exc_info": kwargs.pop("exc_info", False),
        }
        return msg, information


class StructuralFormatter(logging.Formatter):
    def __init__(self, formatter: logging.Formatter | None = None) -> None:
        self.formatter = formatter or logging.Formatter(logging.BASIC_FORMAT)

    def format(self, record: logging.LogRecord) -> str:
        if not getattr(record, "structual", False):
            return self.formatter.format(record)
        d = {
            "level": record.levelname,
            "time": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(record.created)),
            "caller": record.name,
            "msg": record.msg,
        }
        if record.exc_info:
            d["stack"] = self.formatter.formatException(record.exc_info)
        if record.stack_info:
            d["stack"] = self.formatter.formatStack(record.stack_info)
        d.update(record.kwargs)  # type: ignore[attr-defined] # Loggerで拡張追加されているため
        # ローカルではstackをそのまま出力する
        if "stack" in d and is_local:
            print(d["stack"])
        return json.dumps(d)

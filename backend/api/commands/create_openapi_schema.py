from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.routing import APIRoute
import yaml

from api.app import administrator_api, backend_api, external_api

OpenAPISchema = dict[str, Any]


def replace_const_with_enum(schema: OpenAPISchema):
    for item in schema.values():
        if isinstance(item, dict):
            if "const" in item:
                item["enum"] = [item["const"]]
                item["type"] = "string"
                del item["const"]
            replace_const_with_enum(item)


def snake_to_upper_camel(snake_str: str):
    words = snake_str.split("_")
    return "".join(word.capitalize() for word in words)


def create_operation_id(app: FastAPI):
    for route in app.routes:
        if isinstance(route, APIRoute):
            route.operation_id = snake_to_upper_camel(route.name)


if __name__ == "__main__":
    apis = [backend_api, external_api, administrator_api]
    for api in apis:
        create_operation_id(api)
        openapi_schema = api.openapi()
        replace_const_with_enum(openapi_schema)

        with Path(f"/app/api/controllers/{api.title}/openapi/openapi.yml").open("w") as f:
            yaml.dump(openapi_schema, f, default_flow_style=False, allow_unicode=True)

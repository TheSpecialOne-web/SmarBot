from fastapi import Request
from fastapi.routing import APIRoute


def get_url_rule_from_request(request: Request) -> str:
    route = request.scope.get("route", None)
    if route is None:
        raise ValueError("Route not found in request scope")
    if not isinstance(route, APIRoute):
        raise ValueError("Route is not an instance of APIRoute")
    return route.path

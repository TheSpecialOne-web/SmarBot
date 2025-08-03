from azure.core.exceptions import ClientAuthenticationError, ServiceRequestError
from httpx import RemoteProtocolError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


def retry_azure_auth_error(func):
    return retry(
        retry=retry_if_exception_type((ClientAuthenticationError)),
        reraise=True,
        wait=wait_exponential(),
        stop=stop_after_attempt(3),
    )(func)


def retry_remote_protocol_error(func):
    return retry(
        retry=retry_if_exception_type((RemoteProtocolError)),
        reraise=True,
        wait=wait_exponential(),
        stop=stop_after_attempt(3),
    )(func)


def retry_azure_service_error(func):
    return retry(
        retry=retry_if_exception_type((ServiceRequestError)),
        reraise=True,
        wait=wait_exponential(),
        stop=stop_after_attempt(3),
    )(func)

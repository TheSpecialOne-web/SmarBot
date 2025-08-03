from azure.core.exceptions import ClientAuthenticationError
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

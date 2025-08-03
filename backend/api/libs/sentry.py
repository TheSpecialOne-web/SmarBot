import os

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

SENTRY_ENV = os.environ.get("SENTRY_ENV", "localhost")


def init_sentry():
    if SENTRY_ENV == "localhost":
        return
    sentry_sdk.init(
        dsn="https://9602bed59ab7a8d88d8f9c1ae976416d@o4507856054779904.ingest.us.sentry.io/4507856511696896",
        environment=SENTRY_ENV,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
        integrations=[
            StarletteIntegration(transaction_style="url"),
            FastApiIntegration(transaction_style="url"),
        ],
    )

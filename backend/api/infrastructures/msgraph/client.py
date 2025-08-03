# -*- coding:utf-8 -*-
import os

import requests

EMAIL_SENDER_TENANT_ID = os.environ.get("EMAIL_SENDER_TENANT_ID")
EMAIL_SENDER_CLIENT_ID = os.environ.get("EMAIL_SENDER_CLIENT_ID")
EMAIL_SENDER_CLIENT_SECRET = os.environ.get("EMAIL_SENDER_CLIENT_SECRET")


def get_access_token() -> str:
    data = {
        "grant_type": "client_credentials",
        "client_id": EMAIL_SENDER_CLIENT_ID,
        "scope": "https://graph.microsoft.com/.default",
        "client_secret": EMAIL_SENDER_CLIENT_SECRET,
    }
    response = requests.post(
        f"https://login.microsoftonline.com/{EMAIL_SENDER_TENANT_ID}/oauth2/v2.0/token",
        data=data,
    )
    token = response.json()["access_token"]
    return token

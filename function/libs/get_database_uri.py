import os

from azure.identity import DefaultAzureCredential

from libs.retry import retry_azure_auth_error

GET_DB_TOKEN_URL = "https://ossrdbms-aad.database.windows.net/.default"
app_env = os.environ.get("APP_ENV", "localhost")
db_host = os.environ.get("DB_HOST", "")
db_name = os.environ.get("DB_NAME", "")
db_user = os.environ.get("DB_USER", "")


@retry_azure_auth_error
def get_database_uri():
    if app_env == "localhost":
        password = os.environ.get("DB_PASSWORD")
        return f"postgresql://{db_user}:{password}@{db_host}/{db_name}?client_encoding=utf8"
    azure_credential = DefaultAzureCredential()
    token = azure_credential.get_token(GET_DB_TOKEN_URL).token
    return f"postgresql://{db_user}:{token}@{db_host}:5432/{db_name}?client_encoding=utf8"

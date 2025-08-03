from enum import Enum
import os


class AppEnv(str, Enum):
    LOCALHOST = "localhost"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

    def is_localhost(self) -> bool:
        return self == AppEnv.LOCALHOST

    def is_development(self) -> bool:
        return self == AppEnv.DEVELOPMENT

    def is_staging(self) -> bool:
        return self == AppEnv.STAGING

    def is_production(self) -> bool:
        return self == AppEnv.PRODUCTION


app_env = AppEnv(os.environ.get("APP_ENV", AppEnv.LOCALHOST))

from functools import lru_cache
from typing import Dict, Any, Optional

from lottery_api.lib.setting import EnvironmentSettings


class Settings(EnvironmentSettings):
    # JWT settings
    jwt_public_key: str
    jwt_private_key: Optional[str] = None


@lru_cache()
def get_settings():
    return Settings()

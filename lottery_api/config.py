from functools import lru_cache
from typing import Dict, Any

from lottery_api.lib.setting import EnvironmentSettings


class Settings(EnvironmentSettings):
    pass


@lru_cache()
def get_settings():
    return Settings()

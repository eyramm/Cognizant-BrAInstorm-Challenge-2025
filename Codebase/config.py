import os

from dotenv import load_dotenv

load_dotenv()


def _bool_env(var_name: str, default: str = "false") -> bool:
    return os.getenv(var_name, default).lower() == "true"


class Config:
    DEBUG = _bool_env("FLASK_DEBUG", "false")
    TESTING = False
    DATABASE_URL = os.getenv(
        "DATABASE_URL", "postgresql://eyramm@127.0.0.1/ecoapp"
    )
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_TIMEOUT = float(os.getenv("DB_TIMEOUT", "10"))
    OFF_BASE_URL = os.getenv(
        "OFF_BASE_URL", "https://world.openfoodfacts.org/api/v2/product"
    )
    OFF_API_TIMEOUT = int(os.getenv("OFF_API_TIMEOUT", "10"))

    # Default store location for transportation calculations (Halifax, NS)
    DEFAULT_STORE_LAT = float(os.getenv("DEFAULT_STORE_LAT", "44.6488"))
    DEFAULT_STORE_LON = float(os.getenv("DEFAULT_STORE_LON", "-63.5752"))


class DevelopmentConfig(Config):
    DEBUG = True


config_map = {
    "development": DevelopmentConfig,
    "default": Config,
}


def get_config():
    env = os.getenv("FLASK_ENV", "default")
    return config_map.get(env, Config)

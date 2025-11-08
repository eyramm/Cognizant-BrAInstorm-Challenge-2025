import os


class Config:
    DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    TESTING = False


class DevelopmentConfig(Config):
    DEBUG = True


config_map = {
    "development": DevelopmentConfig,
    "default": Config,
}


def get_config():
    env = os.getenv("FLASK_ENV", "default")
    return config_map.get(env, Config)

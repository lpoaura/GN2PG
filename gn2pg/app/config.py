"""
GN2GG global settings file
"""
import logging
import logging.config
import sys
from pathlib import Path

import toml
from decouple import Config, RepositoryEnv

from gn2pg import _
from gn2pg.app.env import SETTINGS_FILE
from gn2pg.env import ENVDIR

logger = logging.getLogger(__name__)


# SETTINGS.INI
settings_config = Config(RepositoryEnv(SETTINGS_FILE))

# SETTINGS for config.toml in order to get [DB] settings
config_toml_file = settings_config("GN2PG_CONFIG_NAME")
toml_dst = str(ENVDIR / config_toml_file)
if Path(toml_dst).is_file():
    ENVDIR.mkdir(exist_ok=True)
else:
    logger.warning(_("%s file doesn't exist. Check the filename at the path %s"), toml_dst, ENVDIR)
    sys.exit(0)
gn2pg_config = toml.load(toml_dst, _dict=dict)["db"]

settings_config = Config(RepositoryEnv(SETTINGS_FILE))
# SET CONFIG ENV VARIABLE
DATABASES = {
    "default": {
        "ENGINE": "postgresql",
        "NAME": gn2pg_config["db_name"],
        "USER": gn2pg_config["db_user"],
        "PASSWORD": gn2pg_config["db_password"],
        "HOST": gn2pg_config["db_host"],
        "PORT": gn2pg_config["db_port"],
    }
}

DEBUG = settings_config("DEBUG", default=False)
ENV = settings_config("ENV", default="production")
APPLICATION_ROOT = settings_config("APPLICATION_ROOT", default="/gn2pg")


class AppConfig:
    ENV: str
    APPLICATION_ROOT: str
    DEBUG: bool
    SQLALCHEMY_DATABASE_URI: str
    DATABASE: dict

    def __init__(self):
        self.ENV = ENV
        self.APPLICATION_ROOT = APPLICATION_ROOT
        self.DEBUG = DEBUG
        self.DATABASE = DATABASES["default"]
        self.set_database_uri()

    def set_database_uri(self):
        DB = self.DATABASE
        self.SQLALCHEMY_DATABASE_URI = f"{DB['ENGINE']}://{DB['USER']}:{DB['PASSWORD']}@{DB['HOST']}:{DB['PORT']}/{DB['NAME']}"


FlaskConfig = AppConfig()

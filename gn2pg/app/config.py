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
TOML_DST = str(ENVDIR / config_toml_file)
if Path(TOML_DST).is_file():
    ENVDIR.mkdir(exist_ok=True)
else:
    logger.warning(_("%s file doesn't exist. Check the filename at the path %s"), TOML_DST, ENVDIR)
    sys.exit(0)
gn2pg_config = toml.load(TOML_DST, _dict=dict)["db"]

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
    """App config class"""

    env: str
    application_root: str
    debug: bool
    sqlalchemy_database_uri: str
    database: dict

    def __init__(self):
        self.env = ENV
        self.application_root = APPLICATION_ROOT
        self.debug = DEBUG
        self.database = DATABASES["default"]
        self.set_database_uri()

    def set_database_uri(self):
        """define database uri"""
        db = self.database
        self.sqlalchemy_database_uri = (
            f"{db['ENGINE']}://"
            + f"{db['USER']}:{db['PASSWORD']}@{db['HOST']}:{db['PORT']}/{db['NAME']}"
        )


FlaskConfig = AppConfig()

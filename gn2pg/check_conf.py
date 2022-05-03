#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""TOML validation tools"""

import logging
from typing import Any, Dict

from schema import Optional, Schema
from toml import load

from . import _, __version__
from .env import ENVDIR
from .utils import coalesce_in_dict, simplify

logger = logging.getLogger("transfer_gn.check_conf")


class Gn2PgConfException(Exception):
    """An exception occurred while loading parameters."""


class MissingConfigurationFile(Gn2PgConfException):
    """Incorrect or missing parameter."""


class IncorrectParameter(Gn2PgConfException):
    """Incorrect or missing parameter."""


_ConfType = Dict[str, Any]

_ConfSchema = Schema(
    {
        "db": {
            "db_host": str,
            "db_port": int,
            "db_user": str,
            "db_password": str,
            "db_name": str,
            "db_schema_import": str,
            Optional("db_querystring"): dict,
        },
        "source": [
            {
                "name": str,
                "user_name": str,
                "user_password": str,
                "url": str,
                "export_id": int,
                Optional("id_application"): int,
                Optional("enable"): bool,
                Optional("data_type"): str,
                Optional("last_action_date"): str,
                Optional("query_strings"): dict,
            }
        ],
        Optional("tuning"): {
            Optional("max_page_length"): int,
            Optional("max_retry"): int,
            Optional("max_requests"): int,
            Optional("retry_delay"): int,
            Optional("unavailable_delay"): int,
            Optional("lru_maxsize"): int,
        },
    }
)


class Gn2PgSourceConf:
    """Source conf generator"""

    def __init__(self, source: str, config: _ConfType) -> None:
        self._source = source
        try:
            # Source configs
            self._name = config["source"][source]["name"]  # type: str
            self._user_name = config["source"][source][
                "user_name"
            ]  # type: str
            self._user_password = config["source"][source][
                "user_password"
            ]  # type: str
            self._url = config["source"][source]["url"]  # type: str
            self._id_application = coalesce_in_dict(
                config["source"][source], "id_application", 3
            )  # type: int
            self._data_type = coalesce_in_dict(
                config["source"][source],
                "data_type",
                "synthese_with_cd_nomenclature",
            )  # type: str
            self._query_strings = coalesce_in_dict(
                config["source"][source], "query_strings", {}
            )
            self._export_id = config["source"][source][
                "export_id"
            ]  # type: int
            self._enable = (
                True
                if "enable" not in config["source"][source]
                else config["source"][source]["enable"]
            )  # type: bool
            # Database config
            self._db_host = config["db"]["db_host"]  # type: str
            self._db_port = config["db"]["db_port"]  # type: int
            self._db_user = config["db"]["db_user"]  # type: str
            self._db_password = config["db"]["db_password"]  # type: str
            self._db_name = config["db"]["db_name"]  # type: str
            self._db_schema_import = config["db"][
                "db_schema_import"
            ]  # type: str
            self._db_querystring = coalesce_in_dict(
                config["db"], "db_querystring", {}
            )  # type: dict
            if "tuning" in config:
                tuning = config["tuning"]
                self._max_page_length = coalesce_in_dict(
                    tuning, "max_page_length", 1000
                )  # type: int
                self._max_retry = coalesce_in_dict(
                    tuning, "max_retry", 5
                )  # type: int
                self._max_requests = coalesce_in_dict(
                    tuning, "max_requests", 0
                )  # type: int
                self._retry_delay = coalesce_in_dict(
                    tuning, "retry_delay", 5
                )  # type: int
                self._unavailable_delay = coalesce_in_dict(
                    tuning, "unavailable_delay", 600
                )  # type: int
                self._lru_maxsize = coalesce_in_dict(
                    tuning, "lru_maxsize", 32
                )  # type: int

        except Exception:  # pragma: no cover
            logger.exception(_(f"Error creating {source} configuration"))
            raise
        return None

    @property
    def source(self) -> str:
        """Return source list position, used to identify source configuration in config file.

        Returns:
            int: Return source list position
        """
        return self._source

    @property
    def name(self) -> str:
        """Return source name

        Returns:
            str: Source name
        """
        return self._name

    @property
    def std_name(self) -> str:
        """Return a standardized source name, used to tag data source in db

        Returns:
            str: standardized Source name
        """
        return simplify(self._name)

    @property
    def user_name(self) -> str:
        """Return source GeoNature username to login into GeoNature foreign instance

        Returns:
            str: GeoNature user username
        """
        return self._user_name

    @property
    def user_password(self) -> str:
        """Return source GeoNature user password to login into GeoNature foreign instance

        Returns:
            str: GeoNature User password
        """
        return self._user_password

    @property
    def url(self) -> str:
        """Return GeoNature URL, used to access to export

        Returns:
            str: GeoNature URL (https://...)
        """
        return self._url

    @property
    def id_application(self) -> int:
        """Return GeoNature id_application, used to login (CRUVED)

        Returns:
            str: GeoNature id_application, default is 3
        """
        return self._id_application

    @property
    def export_id(self) -> int:
        """Return export id, used to access to export

        Returns:
            int: GeoNature export_id
        """
        return self._export_id

    @property
    def data_type(self) -> int:
        """Return data type (eg. "synthese" or any other type you want), used trigger with conditions, if "synthese",
        then insert data into "gn_synthese.synthese" table

        Returns:
            str: Data type
        """
        return self._data_type.lower()

    @property
    def enable(self) -> bool:
        """Return flag to enable or not source

        Returns:
            bool: True if source is enabled
        """
        return self._enable

    @property
    def query_strings(self) -> dict:
        """Return flag to enable or not source

        Returns:
            dict: Querystrings dictionnary
        """
        return self._query_strings

    @property
    def db_host(self) -> str:
        """Return database host

        Returns:
            str: Database host
        """
        return self._db_host

    @property
    def db_port(self) -> int:
        """Return database port

        Returns:
            int: Database port
        """
        return self._db_port

    @property
    def db_querystring(self) -> dict:
        """Return additional database connection string parameters (eg: ssl_mode)

        Returns:
            dict: Database connection querystrings
        """
        if "application_name" not in self._db_querystring:
            self._db_querystring["application_name"] = "gn2pg_cli"
        return self._db_querystring

    @property
    def db_user(self) -> str:
        """Return database user

        Returns:
            str: Database user
        """
        return self._db_user

    @property
    def db_password(self) -> str:
        """Return database user password

        Returns:
            str: Database user password
        """
        return self._db_password

    @property
    def db_name(self) -> str:
        """Return database name

        Returns:
            str: Database name
        """
        return self._db_name

    @property
    def db_schema_import(self) -> str:
        """Return database import schema

        Returns:
            str: Database import schema
        """
        return self._db_schema_import

    @property
    def max_page_length(self) -> int:
        """Page size limit in an API list request.

        Returns:
            int: Page size
        """
        return self._max_page_length

    @property
    def max_retry(self) -> int:
        """Return database import schema

        Returns:
            int: Database import schema
        """
        return self._max_retry

    @property
    def max_requests(self) -> int:
        """Return database import schema

        Returns:
            int: Database import schema
        """
        return self._max_requests

    @property
    def retry_delay(self) -> int:
        """Return database import schema

        Returns:
            int: Database import schema
        """
        return self._retry_delay

    @property
    def unavailable_delay(self) -> int:
        """Return database import schema

        Returns:
            int: Database import schema
        """
        return self._unavailable_delay

    @property
    def lru_maxsize(self) -> int:
        """Return database import schema

        Returns:
            int: Database import schema
        """
        return self._lru_maxsize


class Gn2PgConf:
    """Read config file and expose list of sources configuration"""

    def __init__(self, file: str) -> None:
        """[summary]

        Args:
            file (str): [description]
        """

        p = ENVDIR / file
        if not p.is_file():
            logger.critical(_(f"File {file} does not exist"))
            raise MissingConfigurationFile

        try:
            logger.info(_(f"Loading TOML configuration {file}"))
            self._config = load(p)
            _ConfSchema.validate(self._config)
        except Exception as e:
            logger.critical(
                f"Incorrect content in YAML configuration {file} : {e}"
            )
            raise

        self._source_list = {}  # type: _ConfType
        i = 0
        for source in self._config["source"]:
            source_name = simplify(source["name"])
            logger.info(
                f"Source \"{source['name']}\" identifier will be \"{source_name}\""
            )

            if source_name in [s for s in self._source_list.keys()]:
                logger.critical(
                    (
                        f"Source #{i + 1} named \"{source['name']}\" (->{source_name}) "
                        f"already used by another source"
                    )
                )
            self._source_list[source_name] = Gn2PgSourceConf(i, self._config)
            logger.debug(
                f"Settings for {source_name} are : {self._source_list[source_name].__dict__}"
            )
            i = i + 1

    @property
    def version(self) -> str:
        """Return version."""
        return __version__

    @property
    def source_list(self) -> _ConfType:
        """Return list of site configurations."""
        return self._source_list

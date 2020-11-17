#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""TOML validation tools"""
import logging
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Union, cast

from schema import Optional, Schema, SchemaError
from toml import TomlDecodeError, load
from .utils import simplify

from . import metadata
from .log_conf import coloredlogs, my_logging_dict

logger = logging.getLogger("transfer_gn.check_conf")
__version__ = metadata.version


class Gn2GnConfException(Exception):
    """An exception occurred while loading parameters."""


class MissingConfigurationFile(Gn2GnConfException):
    """Incorrect or missing parameter."""


class IncorrectParameter(Gn2GnConfException):
    """Incorrect or missing parameter."""


_ConfType = Dict[str, Any]


_ConfSchema = Schema(
    {
        Optional("title"): str,
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
                "export_module_api_url": str,
                "export_id": int,
                Optional("enable"): bool,
            }
        ],
    }
)


class Gn2GnSourceConf:
    """Source conf generator"""

    def __init__(self, source: str, config: _ConfType) -> None:
        self._source = source
        try:
            # Source configs
            self._name = config["source"][source]["name"]  # type: str
            self._user_name = config["source"][source]["user_name"]  # type: str
            self._user_password = config["source"][source]["user_password"]  # type: str
            self._export_module_api_url = config["source"][source][
                "export_module_api_url"
            ]  # type: str
            self._export_id = config["source"][source]["export_id"]  # type: int
            self._enable = (
                True
                if "enabled" not in config["source"][source]
                else config["file"]["enabled"]
            )  # type: bool
            # Database config
            self._db_host = config["db"]["db_host"]  # type: str
            self._db_port = config["db"]["db_port"]  # type: int
            self._db_user = config["db"]["db_user"]  # type: str
            self._db_password = config["db"]["db_password"]  # type: str
            self._db_name = config["db"]["db_name"]  # type: str
            self._db_schema_import = config["db"]["db_schema_import"]  # type: str
            self._db_querystring = (
                None
                if "db_querystring" not in config["source"][source]
                else config["db"]["db_querystring"]
            )  # type: dict

        except Exception:  # pragma: no cover
            logger.exception(f"Error creating {source} configuration")
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
        """Return source name, used to tag data source in db

        Returns:
            str: Source name
        """
        return self._name

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
    def export_module_api_url(self) -> str:
        """Return export module api root URL, used to access to export

        Returns:
            str: export module api URL (https://...)
        """
        return self._export_module_api_url

    @property
    def export_id(self) -> int:
        """Return export id, used to access to export

        Returns:
            int: GeoNature export_id
        """
        return self._export_id

    @property
    def enable(self) -> bool:
        """Return flag to enable or not source

        Returns:
            bool: True if source is enabled
        """
        return self._enable

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


class Gn2GnConf:
    """Read config file and expose list of sources configuration"""

    def __init__(self, file: str) -> None:
        """[summary]

        Args:
            file (str): [description]
        """

        p = Path.home() / file
        if not p.is_file():
            logger.critical(f"File {file} does not exist")
            raise MissingConfigurationFile

        try:
            logger.info(f"Loading TOML configuration {file}")
            self._config = load(p)
            _ConfSchema.validate(self._config)
        except TomlDecodeError:
            logger.critical(f"Incorrect content in YAML configuration {file}")
            logger.critical(f"{sys.exc_info()[1]}")
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
                    f"Source #{i+1} named \"{source['name']}\" (->{source_name}) already used by another source"
                )
            self._source_list[source_name] = Gn2GnSourceConf(i, self._config)
            i = i + 1

    @property
    def version(self) -> str:
        """Return version."""
        return metadata.version

    @property
    def source_list(self) -> _ConfType:
        """Return list of site configurations."""
        return self._source_list

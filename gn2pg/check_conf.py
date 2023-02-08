#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""TOML validation tools"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict

from schema import Optional, Schema
from toml import load

from gn2pg import _, __version__
from gn2pg.env import ENVDIR
from gn2pg.utils import coalesce_in_dict, simplify

logger = logging.getLogger(__name__)


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
            Optional("nb_threads"): int,
        },
    }
)


@dataclass
class Db:
    """Database connection settings"""

    host: str
    user: str
    password: str
    name: str
    port: str = 5432
    schema_import: str = "gn2pg_import"
    querystring: dict = field(default_factory=dict)


@dataclass
class Source:
    """Source connection settings"""

    name: str
    user_name: str
    user_password: str
    url: str
    export_id: int
    data_type: str
    id_application: int = 3
    enable: bool = True
    last_action_date: str = None
    query_strings: dict = field(default_factory=dict)


@dataclass
class Tuning:
    """Tuning settings"""

    max_page_length: int = 1000
    max_retry: int = 5
    max_requests: int = 0
    retry_delay: int = 5
    unavailable_delay: int = 600
    lru_maxsize: int = 32
    nb_threads: int = 1


class Gn2PgSourceConf:
    """Source conf generator"""

    def __init__(self, source: str, config: _ConfType) -> None:
        self._selected_source = source
        try:
            # Source configs
            self._source = Source(
                name=config["source"][source]["name"],
                user_name=config["source"][source]["user_name"],
                user_password=config["source"][source]["user_password"],
                url=config["source"][source]["url"],
                id_application=coalesce_in_dict(config["source"][source], "id_application", 3),
                data_type=coalesce_in_dict(
                    config["source"][source],
                    "data_type",
                    "synthese_with_cd_nomenclature",
                ),
                query_strings=coalesce_in_dict(config["source"][source], "query_strings", {}),
                export_id=config["source"][source]["export_id"],
                enable=(
                    True
                    if "enable" not in config["source"][source]
                    else config["source"][source]["enable"]
                ),
            )

            # Database config
            self._db = Db(
                host=config["db"]["db_host"],
                port=config["db"]["db_port"],
                user=config["db"]["db_user"],
                password=config["db"]["db_password"],
                name=config["db"]["db_name"],
                schema_import=config["db"]["db_schema_import"],
                querystring=coalesce_in_dict(config["db"], "db_querystring", {}),
            )  # type: Db
            if "tuning" in config:
                tuning = config["tuning"]
                self._tuning = Tuning(
                    max_page_length=coalesce_in_dict(tuning, "max_page_length", 1000),
                    max_retry=coalesce_in_dict(tuning, "max_retry", 5),
                    max_requests=coalesce_in_dict(tuning, "max_requests", 0),
                    retry_delay=coalesce_in_dict(tuning, "retry_delay", 5),
                    unavailable_delay=coalesce_in_dict(tuning, "unavailable_delay", 600),
                    lru_maxsize=coalesce_in_dict(tuning, "lru_maxsize", 32),
                    nb_threads=coalesce_in_dict(tuning, "nb_threads", 1),
                )

        except Exception:  # pragma: no cover
            logger.exception(_("Error creating %s configuration"), source)
            raise

    @property
    def source(self) -> str:
        """Return source list position, used to identify source configuration in config file.

        Returns:
            int: Return source list position
        """
        return self._selected_source

    @property
    def name(self) -> str:
        """Return source name

        Returns:
            str: Source name
        """
        return self._source.name

    @property
    def std_name(self) -> str:
        """Return a standardized source name, used to tag data source in db

        Returns:
            str: standardized Source name
        """
        return simplify(self._source.name)

    @property
    def user_name(self) -> str:
        """Return source GeoNature username to login into GeoNature foreign instance

        Returns:
            str: GeoNature user username
        """
        return self._source.user_name

    @property
    def user_password(self) -> str:
        """Return source GeoNature user password to login into GeoNature foreign instance

        Returns:
            str: GeoNature User password
        """
        return self._source.user_password

    @property
    def url(self) -> str:
        """Return GeoNature URL, used to access to export

        Returns:
            str: GeoNature URL (https://...)
        """
        return self._source.url

    @property
    def id_application(self) -> int:
        """Return GeoNature id_application, used to login (CRUVED)

        Returns:
            str: GeoNature id_application, default is 3
        """
        return self._source.id_application

    @property
    def export_id(self) -> int:
        """Return export id, used to access to export

        Returns:
            int: GeoNature export_id
        """
        return self._source.export_id

    @property
    def data_type(self) -> str:
        """Return data type (eg. "synthese" or any other type you want),
        used trigger with conditions, if "synthese", then insert data
        into "gn_synthese.synthese" table

        Returns:
            str: Data type
        """
        return self._source.data_type.lower()

    @property
    def enable(self) -> bool:
        """Return flag to enable or not source

        Returns:
            bool: True if source is enabled
        """
        return self._source.enable

    @property
    def query_strings(self) -> dict:
        """Return flag to enable or not source

        Returns:
            dict: Querystrings dictionnary
        """
        return self._source.query_strings

    @property
    def database(self) -> Db:
        """Return database settings

        :return: _description_
        :rtype: Db
        """
        return self._db

    @property
    def max_page_length(self) -> int:
        """Page size limit in an API list request.

        Returns:
            int: Page size
        """
        return self._tuning.max_page_length

    @property
    def max_retry(self) -> int:
        """Return database import schema

        Returns:
            int: Database import schema
        """
        return self._tuning.max_retry

    @property
    def max_requests(self) -> int:
        """Return database import schema

        Returns:
            int: Database import schema
        """
        return self._tuning.max_requests

    @property
    def retry_delay(self) -> int:
        """Return database import schema

        Returns:
            int: Database import schema
        """
        return self._tuning.retry_delay

    @property
    def unavailable_delay(self) -> int:
        """Return database import schema

        Returns:
            int: Database import schema
        """
        return self._tuning.unavailable_delay

    @property
    def lru_maxsize(self) -> int:
        """Return database import schema

        Returns:
            int: Database import schema
        """
        return self._tuning.lru_maxsize

    @property
    def nb_threads(self) -> int:
        """Get the number of computing threads

        Returns:
            int: The number of computing threads
        """
        return self._tuning.nb_threads


class Gn2PgConf:
    """Read config file and expose list of sources configuration"""

    def __init__(self, file: str) -> None:
        """[summary]

        Args:
            file (str): [description]
        """

        path = ENVDIR / file
        if not path.is_file():
            logger.critical(_("File %s does not exist"), file)
            raise MissingConfigurationFile

        try:
            logger.info(_("Loading TOML configuration %s"), file)
            self._config = load(path)
            _ConfSchema.validate(self._config)
        except Exception as error:
            logger.critical(
                _("Incorrect content in YAML configuration %s : %s"),
                file,
                error,
            )
            raise

        self._source_list = {}  # type: _ConfType
        i = 0
        for source in self._config["source"]:
            source_name = simplify(source["name"])
            logger.info(
                _('Source "%s" identifier will be "%s"'),
                source["name"],
                source_name,
            )

            if source_name in self._source_list:
                logger.critical(
                    (
                        _('Source #%s named "%s" (->%s) already used by another source'),
                        i + 1,
                        source["name"],
                        source_name,
                    )
                )
            self._source_list[source_name] = Gn2PgSourceConf(i, self._config)
            logger.debug(
                _("Settings for %s are : %s"),
                source_name,
                self._source_list[source_name].__dict__,
            )
            i += 1

    @property
    def version(self) -> str:
        """Return version."""
        return __version__

    @property
    def source_list(self) -> _ConfType:
        """Return list of site configurations."""
        return self._source_list

"""Methods to download from VisioNature and store to file.


Methods

- download_taxo_groups      - Download and store taxo groups

Properties

-

"""
import logging
from typing import NoReturn

from . import _, __version__
from .api import DataAPI, DatasetsAPI

logger = logging.getLogger("transfer_gn.download_gn")


class DownloadGnException(Exception):
    """An exception occurred while handling download or store."""


class NotImplementedException(DownloadGnException):
    """Feature not implemented."""


class DownloadGn:
    """Top class, not for direct use.
    Provides internal and template methods."""

    def __init__(
        self, config, api_instance, backend, max_retry=None, max_requests=None
    ) -> NoReturn:
        self._config = config
        self._api_instance = api_instance
        self._backend = backend
        if max_retry is None:
            max_retry = config.max_retry
        if max_requests is None:
            max_requests = config.max_requests
        self._limits = {
            "max_retry": max_retry,
            "max_requests": max_requests,
        }

    @property
    def version(self) -> str:
        """Return version."""
        return __version__

    @property
    def transfer_errors(self) -> int:
        """Return the number of HTTP errors during this session."""
        return self._api_instance.transfer_errors

    @property
    def name(self) -> str:
        """Return the controler name."""
        return self._api_instance.controler

    # ----------------
    # Internal methods
    # ----------------

    # ---------------
    # Generic methods
    # ---------------
    def store(self) -> NoReturn:
        """Store data into Database

        Returns:
            None
        """

        logger.debug(
            _(f"Getting items from controler {self._api_instance.controler}")
        )
        pages = self._api_instance._page_list(
            limit=self._config.max_page_length
        )
        self._backend.log(
            self._config.source,
            self._api_instance.controler,
            self._api_instance.transfer_errors,
            self._api_instance.http_status,
        )
        progress = 0
        for p in pages:
            resp = self._api_instance.get_page(p)
            items = resp["items"]
            len_items = len(items)
            total_len = resp["total_filtered"]
            progress = progress + len_items
            logger.info(
                f"Storing {len_items} datas ({progress}/{total_len} "
                f"{round((progress/total_len)*100,2)}%)"
                f"from {self._config.name} {self._api_instance.controler}"
            )
            self._backend.store_data(
                self._api_instance.controler, resp["items"]
            )

    def update(self, since: str) -> NoReturn:
        """[summary]

        Args:
            since (str): DateTime limit to update.

        Returns:
            [type]: [description]
        """
        logger.debug(
            _(f"Updating items from controler {self._api_instance.controler}")
        )


class Data(DownloadGn):
    """Implement store from observations controler.

    Methods
    - store               - Download by page and store to json

    """

    def __init__(self, config, backend, max_retry=None, max_requests=None):
        super().__init__(
            config, DataAPI(config), backend, max_retry, max_requests
        )
        return None


class Datasets(DownloadGn):
    """Implement store from places controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(self, config, backend, max_retry=None, max_requests=None):
        super().__init__(
            config, DatasetsAPI(config), backend, max_retry, max_requests
        )
        return None

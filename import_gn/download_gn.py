"""Methods to download from VisioNature and store to file.


Methods

- download_taxo_groups      - Download and store taxo groups

Properties

-

"""
import logging

from . import _, __version__
from .api import DatasetsAPI, SyntheseAPI

logger = logging.getLogger("transfer_gn.download_gn")


class DownloadGnException(Exception):
    """An exception occurred while handling download or store. """


class NotImplementedException(DownloadGnException):
    """Feature not implemented."""


class DownloadGn:
    """Top class, not for direct use.
    Provides internal and template methods."""

    def __init__(self, config, api_instance, backend, max_retry=None, max_requests=None):
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
        return None

    @property
    def version(self):
        """Return version."""
        return __version__

    @property
    def transfer_errors(self):
        """Return the number of HTTP errors during this session."""
        return self._api_instance.transfer_errors

    @property
    def name(self):
        """Return the controler name."""
        return self._api_instance.controler

    # ----------------
    # Internal methods
    # ----------------

    # ---------------
    # Generic methods
    # ---------------
    def store(self, opt_params_iter=None):
        """Download from GN by API and store json to DB.

        Calls  GeoNature API, convert to json and call backend to store.

        Parameters
        ----------
        opt_params_iter : iterable or None
            Provides opt_params values.

        """
        # GET from API
        logger.debug(_(f"Getting items from controler {self._api_instance.controler}"))
        i = 0
        if opt_params_iter is None:
            opt_params_iter = iter([None])
        for opt_params in opt_params_iter:
            i += 1
            logger.debug(f"opt_params = {opt_params}")
            pages = self._api_instance.get_page_list(opt_params)
            i = 1
            self._backend.log(
                self._config.source,
                self._api_instance.controler,
                self._api_instance.transfer_errors,
                self._api_instance.http_status,
                f"opt_params = {opt_params}",
            )
            progress = 0
            for p in pages:
                resp = self._api_instance.get_page(p)
                items = resp["items"]
                len_items = len(items)
                total_len = resp["total_filtered"]
                progress = progress + len_items
                logger.info(
                    f"Storing {len_items} datas ({progress}/{total_len} {(progress/total_len)*100}%)"
                    f" from {self._config.name} {self._api_instance.controler}"
                )
                self._backend.store(self._api_instance.controler, resp["items"])
        return None


class Synthese(DownloadGn):
    """Implement store from observations controler.

    Methods
    - store               - Download by page and store to json

    """

    def __init__(self, config, backend, max_retry=None, max_requests=None):
        super().__init__(config, SyntheseAPI(config), backend, max_retry, max_requests)
        return None


class Datasets(DownloadGn):
    """Implement store from places controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(self, config, backend, max_retry=None, max_requests=None):
        super().__init__(config, DatasetsAPI(config), backend, max_retry, max_requests)
        return None

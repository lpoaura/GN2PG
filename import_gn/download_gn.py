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
            log_msg = _(f"Iteration {i}, opt_params = {opt_params}")
            logger.debug(log_msg)
            items_dict = self._api_instance.get(opt_params)
            # Call backend to store generic log
            self._backend.log(
                self._config.source,
                self._api_instance.controler,
                self._api_instance.transfer_errors,
                self._api_instance.http_status,
                log_msg,
            )
            # Call backend to store results
            self._backend.store(self._api_instance.controler, items_dict)

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

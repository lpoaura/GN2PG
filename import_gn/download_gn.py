"""Methods to download from VisioNature and store to file.


Methods

- download_taxo_groups      - Download and store taxo groups

Properties

-

"""
import logging
from datetime import datetime, timedelta

from geonature.api import SyntheseAPI, DatasetsAPI
from import_gn.regulator import PID

from . import _, __version__

logger = logging.getLogger("transfer_vn.download_vn")


class DownloadGnException(Exception):
    """An exception occurred while handling download or store. """


class NotImplementedException(DownloadGnException):
    """Feature not implemented."""


class DownloadGn:
    """Top class, not for direct use.
    Provides internal and template methods."""

    def __init__(
        self, config, api_instance, backend, max_retry=None, max_requests=None
    ):
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
        """Download from VN by API and store json to file.

        Calls  biolovision_api, convert to json and call backend to store.

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
            items_dict = self._api_instance.api_list(opt_params=opt_params)
            # Call backend to store generic log
            self._backend.log(
                self._config.source,
                self._api_instance.controler,
                self._api_instance.transfer_errors,
                self._api_instance.http_status,
                log_msg,
            )
            # Call backend to store results
            self._backend.store(self._api_instance.controler, str(i), items_dict)

        return None


class Synthese(DownloadGn):
    """Implement store from observations controler.

    Methods
    - store               - Download by page and store to json

    """

    def __init__(self, config, backend, max_retry=None, max_requests=None):
        super().__init__(config, SyntheseAPI(config), backend, max_retry, max_requests)
        return None

    def _store_search(self):
        """Download from GeoNature by API search and store json to file."""
        # GET from API
        logger.debug(
            _(
                f"Getting data from controler {self._api_instance.controler}, using API search"
            ),
        )
        logger.debug(_(f"source : {self._config.name }"))

        # When to start download interval
        seq = 1

        q_param = {}
        items_dict = self._api_instance.api_search(self._config, q_param)
        # Call backend to store results
        nb_obs = self._backend.store(
            self._api_instance.controler,
            items_dict,
        )
        date4log = start_date.strftime("%d/%m/%Y")
        log_msg = _(
            f"{self._config.source} => Iter: {seq}, {nb_obs} obs, date: {date4log}, interval: {str(delta_days)}"
        )
        # Call backend to store log
        self._backend.log(
            self._config.source,
            self._api_instance.controler,
            self._api_instance.transfer_errors,
            self._api_instance.http_status,
            log_msg,
        )
        logger.info(log_msg)
        seq += 1
        return None

    def store(self, method="search"):
        """Download from VN by API and store json to database."""
        # Get the list of taxo groups to process
        logger.info(_(f"0 => Downloading data"))
        return None


class Datasets(DownloadGn):
    """Implement store from places controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(self, config, backend, max_retry=None, max_requests=None):
        super().__init__(config, DatasetsAPI(config), backend, max_retry, max_requests)
        return None

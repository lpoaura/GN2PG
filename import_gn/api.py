"""Provide python interface to GeoNature API.


Methods, see each class

Properties:

- transfer_errors            - Return number of HTTP errors

Exceptions:

- BiolovisionApiException    - General exception
- HTTPError                  - HTTP protocol error
- MaxChunksError             - Too many chunks returned from API calls
- IncorrectParameter         - Incorrect or missing parameter

"""
import json
import logging
from math import floor
from urllib.parse import urlencode

import requests

from . import _, __version__

logger = logging.getLogger("transfer_gn.geonature_api")


class APIException(Exception):
    """An exception occurred while handling your request."""


class HTTPError(APIException):
    """An HTTP error occurred."""


class BaseAPI:
    """Top class, not for direct use. Provides internal and template methods."""

    def __init__(self, config, controler, max_retry=None, max_requests=None):
        self._config = config
        if max_retry is None:
            max_retry = config.max_retry
        if max_requests is None:
            max_requests = config.max_requests
        self._limits = {"max_retry": max_retry, "max_requests": max_requests}
        self._transfer_errors = 0
        self._http_status = 0
        self._ctrl = controler
        logger.debug(f"controler is {self._ctrl}")
        url = config.url if config.url[-1:] == "/" else config.url + "/"
        self._api_url = url + "api/"  # API Url

        # init session
        self._session = requests.Session()
        self._session.headers = {"Content-Type": "application/json"}
        auth_payload = json.dumps(
            {
                "login": config.user_name,
                "password": config.user_password,
                "id_application": config.id_application,
            }
        )
        login = self._session.post(
            self._api_url + "auth/login",
            data=auth_payload,
        )
        try:
            if login.status_code == 200:
                logger.info(f"Successfully logged in into GeoNature named {self._config.name}")
            else:
                logger.critical(
                    (
                        f"Log in GeoNature named {self._config.name} failed with status code"
                        f"{login.status_code}, cause: {json.loads(login.content)['msg']}"
                    )
                )

        except Exception as e:
            logger.critical(f"Session failed ({e})")
            raise HTTPError(login.status_code)

        #  Find exports api path
        try:
            m = self._session.get(self._api_url + "gn_commons/modules")
            logger.info(_(f"Modules API status code is {m.status_code} for url {m.url}"))
            if m.status_code == 200:
                modules = json.loads(m.content)
                for item in modules:
                    if item["module_code"] == "EXPORTS":
                        self._export_api_path = item["module_path"]
                        logger.debug(f"Export api path is {self._export_api_path}")
                        break
            else:
                logger.critical(
                    (
                        f"Get GeoNature modules failed with status code {m.status_code}, "
                        f"cause: {json.loads(m.content)['msg']}"
                    )
                )
        except Exception as e:
            logger.critical(f"Find export module failed, {e}")
            raise HTTPError(login.status_code)

    @property
    def version(self) -> str:
        """Return version."""
        return __version__

    @property
    def transfer_errors(self) -> int:
        """Return the number of HTTP errors during this session."""
        return self._transfer_errors

    @property
    def http_status(self) -> int:
        """Return the latest HTTP status code."""
        return self._http_status

    @property
    def controler(self) -> str:
        """Return the controler name."""
        return self._ctrl

    def _url(self, params: dict = None) -> str:
        """Generate API URL with QueryStrings if params

        Args:
            params (dict, optional): dict of querystring parameters. Defaults to None.

        Returns:
            str: export API URL
        """
        export_url = self._api_url + self._export_api_path + "/api/" + str(self._config.export_id)
        if params:
            export_url = export_url + "?" + urlencode(params)
        return export_url

    def get(self, params, **kwargs):
        """Query for a single entity of the given controler.

        Calls  /ctrl/id API.

        Parameters
        ----------
        id_entity : str
            entity to retrieve.
        **kwargs :
            optional URL parameters, empty by default.
            See Biolovision API documentation.

        Returns
        -------
        json : dict or None
            dict decoded from json if status OK, else None
        """
        params = {}
        for key, value in kwargs.items():
            params[key] = value
        # GET from API
        session = self._session
        api_url = self._url(params)
        data = []
        r = session.get(
            url=api_url,
        )
        if r.status_code == 200:
            resp = r.json()
            total_filtered = resp["total_filtered"]
            total_pages = floor(total_filtered / resp["limit"])
            logger.debug(
                _(
                    f"API {self._url(params)} contains {total_filtered}"
                    f" data in {total_pages+1} page(s)"
                )
            )
            for p in range(total_pages + 1):
                params["offset"] = p
                logger.debug(f"querying url {self._url(params)}")
                pr = session.get(url=self._url(params))
                presp = pr.json()
                items = presp["items"]
                data += items
                logger.debug(f"Download page {p}")
        return data


class SyntheseAPI(BaseAPI):
    def __init__(self, config, max_retry=None, max_requests=None):
        super().__init__(config, "synthese", max_retry, max_requests)


class DatasetsAPI(BaseAPI):
    def __init__(self, config, max_retry=None, max_requests=None):
        super().__init__(config, "datasets", max_retry, max_requests)

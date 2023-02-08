"""Provide python interface to GeoNature API.


Methods, see each class

Properties:

- transfer_errors            - Return number of HTTP errors

Exceptions:

- APIException    - General exception
- HTTPError                  - HTTP protocol error

"""
import json
import logging
import math
from typing import Optional
from urllib.parse import urlencode

import requests

from gn2pg import _, __version__

logger = logging.getLogger(__name__)


class APIException(Exception):
    """An exception occurred while handling your request."""


class HTTPError(APIException):
    """An HTTP error occurred."""


class BaseAPI:
    """Top class, not for direct use.
    Provides internal and template methods to use GeoNature API."""

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
        logger.debug(_("controler is %s"), self._ctrl)
        self._api_url = config.url + "/" * (not config.url.endswith("/")) + "api/"

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
                logger.info(
                    "Successfully logged in into GeoNature named %s",
                    self._config.name,
                )
            else:
                logger.critical(
                    (
                        "Log in GeoNature named %s failed with status code %s, cause: %s",
                        self._config.name,
                        login.status_code,
                        json.loads(login.content)["msg"],
                    )
                )

        except Exception as error:
            logger.critical("Session failed (%s)", error)
            raise HTTPError(login.status_code) from error

        #  Find exports api path
        try:
            modules_list = self._session.get(self._api_url + "gn_commons/modules")
            logger.info(
                _("Modules API status code is %s for url %s"),
                modules_list.status_code,
                modules_list.url,
            )
            if modules_list.status_code == 200:
                modules = json.loads(modules_list.content)
                for item in modules:
                    if item["module_code"] == "EXPORTS":
                        self._export_api_path = item["module_path"]
                        logger.debug(_("Export api path is %s"), self._export_api_path)
                        break
            else:
                logger.critical(
                    _("Get GeoNature modules failed with status code %s, cause: %s"),
                    modules_list.status_code,
                    json.loads(modules_list.content)["msg"],
                )

        except Exception as error:
            logger.critical(_("Find export module failed, %s"), error)
            raise HTTPError(login.status_code) from error

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

    def _url(self, kind: str = "data", params: dict = None) -> str:
        """Generate export API URL with QueryStrings if params.

        Args:
            params (dict, optional): dict of querystring parameters. Defaults to None.

        Returns:
            str: export API URL.
        """
        if kind == "data":
            url = f"{self._api_url}{self._export_api_path}/api/{str(self._config.export_id)}"
        elif kind == "log":
            url = f"{self._api_url}synthese/log"
        else:
            return None
        if params is not None:
            logger.debug("params %s", params)
            url = url + "?" + urlencode(params)
        return url

    def page_list(
        self,
        params: dict,
        kind: str = "data",
    ) -> Optional[list]:
        """List offset pages to download data, based on API "total_filtered" and "limit" values

        Args:
            **kwargs : Keyword args to filter data from API (cf. swagger API doc)

        Returns:
            list: url page list
        """
        # GET from API
        session = self._session

        # Check kind value
        if self._url(kind) is None:
            return None

        api_url = self._url(kind, params)

        response = session.get(url=api_url, params={**params, **{"limit": 1}})
        logger.debug(
            _("Defining page_list from %s with status code %s"),
            api_url,
            response.status_code,
        )

        if response.status_code == 200:
            resp = response.json()
            total_filtered = resp["total_filtered"]
            total_pages = math.ceil(total_filtered / params.get("limit"))
            logger.debug(
                _("API %s contains %s data in %s page(s)"),
                api_url,
                total_filtered,
                total_pages,
            )

            page_list = (self._url(kind, {**params, **{"offset": p}}) for p in range(total_pages))
            return page_list
        logger.info(_("No data available from from %s"), self._config.name)
        return None

    def get_page(self, page_url: str) -> Optional[dict]:
        """Get data from one API page

        Args:
            page_url (str): page URL

        Returns:
            dict: Datas as dict
        """

        try:
            logger.info(_("Download page %s"), page_url)
            session = self._session
            page_request = session.get(url=page_url)
            resp = page_request.json()
            return resp
        except APIException as error:
            logger.critical(_("Download data from %s failed"), page_url)
            logger.critical(str(error))
            return None


class DataAPI(BaseAPI):
    """Data API"""

    def __init__(self, config, max_retry=None, max_requests=None):
        super().__init__(config, "data", max_retry, max_requests)

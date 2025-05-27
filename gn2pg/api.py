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
from typing import List, Optional
from urllib.parse import urlencode

import requests
from requests.adapters import HTTPAdapter, Retry
from requests.exceptions import HTTPError, RetryError

from gn2pg import _, __version__

logger = logging.getLogger(__name__)


class APIException(Exception):
    """An exception occurred while handling your request."""


class BaseAPI:
    """Top class, not for direct use.
    Provides internal and template methods to use GeoNature API."""

    def __init__(
        self,
        config,
        controler,
    ):
        self._config = config
        max_retry = config.max_retry
        max_requests = config.max_requests
        retry_delay = config.retry_delay
        self._limits = {"max_retry": max_retry, "max_requests": max_requests}
        self._transfer_errors = 0
        self._http_status = 0
        self._ctrl = controler
        logger.debug(_("controler is %s"), self._ctrl)
        self._api_url = config.url + "/" * (not config.url.endswith("/")) + "api/"

        # init session
        self._session = requests.Session()
        retries = Retry(
            total=max_retry,
            backoff_factor=retry_delay,
            status_forcelist=[500, 501, 502, 503, 504],
        )
        self._session.mount("https://", HTTPAdapter(max_retries=retries))
        self._session.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
        }
        auth_payload = {
            "login": config.user_name,
            "password": config.user_password,
        }

        # logger.debug(
        #     "login.status_code %s, login.content %s, payload.auth_payload %s",
        #     login.status_code,
        #     login.content,
        #     auth_payload,
        # )
        try:
            login = self._session.post(
                self._api_url + "auth/login",
                json=auth_payload,
            )
            login.raise_for_status()
            if login.status_code == 200:
                logger.info(
                    _("Successfully logged in into GeoNature named %s"),
                    self._config.name,
                )
        except HTTPError as error:
            logger.critical(
                # _("Session failed (%s), HTTP status code is %s"), e, e.response.status_code
                _("Login into GeoNature from source %s failed with status code %s, message: %s"),
                self._config.name,
                error.response.status_code,
                error.response.json(),
            )
            raise error

        #  Find exports api path
        try:
            modules_list = self._session.get(self._api_url + "gn_commons/modules")
            logger.info(
                _("Modules API status code is %s for url %s"),
                modules_list.status_code,
                modules_list.url,
            )
            modules_list.raise_for_status()
            if modules_list.status_code == 200 and "login?next=" not in modules_list.url:
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

        except HTTPError as error:
            logger.critical(
                _("Looking for export module failed for source %s , %s"), self._config.name, error
            )
            raise error

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
    def controler(self) -> Optional[str]:
        """Return the controler name."""
        return self._ctrl

    def _url(self, kind: str = "data", params: Optional[dict] = None) -> str:
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
        pagination_param: str = "offset",
    ) -> tuple[Optional[List[str]], int]:
        """List offset pages to download data, based on API "total_filtered" and "limit" values

        :param params: Querystrings
        :type params: dict
        :param kind: kind of data, defaults to "data"
        :type kind: str, optional
        :param pagination_param: Pagination parameter key
        :type pagination_param: str, optional
        :return: url page list
        :rtype: Optional[List[str]]
        """
        # GET from API
        session = self._session

        # Check kind value
        if self._url(kind) is None:
            return None, 0, None

        api_url = self._url(kind, params)
        try:
            response = session.get(url=api_url, params={**params})
            status_code = response.status_code
            if response.status_code == 200:
                resp = response.json()
                total_filtered = (
                    resp["total_filtered"] if "total_filtered" in resp else resp["total"]
                )
                limit = resp["limit"]
                total_pages = math.ceil(total_filtered / limit)
                logger.debug(
                    _("API %s contains %s data in %s page(s)"),
                    api_url,
                    total_filtered,
                    total_pages,
                )
                if total_filtered > 0:
                    page_list = list(
                        self._url(
                            kind,
                            {
                                **params,
                                **{pagination_param: p + 1 if pagination_param == "page" else p},
                            },
                        )
                        for p in range(total_pages)
                    )
                    return page_list, total_filtered, status_code
        except RetryError as e:
            last_response = e.response
            status_code = last_response.status_code if last_response is not None else None
            raise e

        return None, 0, status_code

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

    def __init__(self, config):
        super().__init__(config, "data")

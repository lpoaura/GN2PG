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
from requests.exceptions import HTTPError, InvalidSchema, RequestException

from gn2pg import _, __version__
from gn2pg.check_conf import Gn2PgSourceConf

logger = logging.getLogger(__name__)


class APIException(Exception):
    """An exception occurred while handling your request."""


class ExportModuleNotFoundError(Exception):
    """Custom exception raised when the EXPORTS module is not found."""


class BaseAPI:
    """Top class, not for direct use.
    Provides internal and template methods to use GeoNature API."""

    def __init__(
        self,
        config: Gn2PgSourceConf,
        controler: str,
    ):
        self._config: Gn2PgSourceConf = config
        max_retry = config.max_retry
        max_requests = config.max_requests
        self._timeout = getattr(config, "http_timeout", (10, 120))
        self._limits = {"max_retry": max_retry, "max_requests": max_requests}
        self._transfer_errors = 0
        self._http_status = 0
        self._ctrl = controler
        logger.debug(_("controler is %s"), self._ctrl)
        self._api_url = config.url + "/" * (not config.url.endswith("/")) + "api/"

        self._session = self._create_session(config)

        auth_payload = {
            "login": config.user_name,
            "password": config.user_password,
        }

        try:
            login = self._session.post(
                self._api_url + "auth/login",
                json=auth_payload,
                timeout=self._timeout,
            )
            login.raise_for_status()
            if login.status_code == 200:
                logger.info(
                    _("Successfully logged in into GeoNature named %s"),
                    self._config.name,
                )
        except HTTPError as error:
            logger.critical(
                _(
                    "Login into GeoNature from source %(source)s failed with status code "
                    "%(status_code)s, message: %(message)s"
                ),
                {
                    "source": self._config.name,
                    "status_code": error.response.status_code,
                    "message": error.response.json(),
                },
            )
            raise error
        except InvalidSchema as error:
            logger.critical(
                _("There is probably an error on source URL for %(source)s, %(error)s"),
                {"source": self._config.name, "error": error},
            )
            raise error

        #  Find exports api path
        self._export_api_path = None  # Initialize the variable
        try:
            modules_list = self._session.get(
                self._api_url + "gn_commons/modules", timeout=self._timeout
            )
            logger.info(
                _("Modules API status code is %(status_code)s for url %(url)s"),
                {"status_code": modules_list.status_code, "url": modules_list.url},
            )
            modules_list.raise_for_status()
            if modules_list.status_code == 200 and "login?next=" not in modules_list.url:
                modules = json.loads(modules_list.content)
                for item in modules:
                    if item["module_code"] == "EXPORTS":
                        self._export_api_path = item["module_path"]
                        logger.debug(_("Export api path is %s"), self._export_api_path)
                        break
                if self._export_api_path is None:
                    logger.critical(
                        _(
                            "EXPORTS module not found in the modules list for export %(export)s. "
                            "User %(user)s may not have required permissions on module."
                        ),
                        {"export": self._config.name, "user": self._config.user_name},
                    )
                    raise ExportModuleNotFoundError("Module not found")
            else:
                logger.critical(
                    _(
                        "Get GeoNature modules failed with status code %(status_code)s, "
                        "cause: %(cause)s"
                    ),
                    {
                        "status_code": modules_list.status_code,
                        "cause": json.loads(modules_list.content)["msg"],
                    },
                )

        except HTTPError as error:
            logger.critical(
                _("Looking for export module failed for source %(source)s, %(error)s"),
                {"source": self._config.name, "error": error},
            )
            raise error

    @staticmethod
    def _create_session(config: Gn2PgSourceConf) -> requests.Session:
        """Create an HTTP session configured for concurrent, resilient transfers."""
        session = requests.Session()
        retries = Retry(
            total=config.max_retry,
            connect=config.max_retry,
            read=config.max_retry,
            status=config.max_retry,
            backoff_factor=config.retry_delay,
            status_forcelist=[429, 500, 501, 502, 503, 504],
            allowed_methods=frozenset({"GET", "HEAD", "OPTIONS", "POST"}),
            respect_retry_after_header=True,
            backoff_jitter=1.0,
        )
        pool_size = max(1, config.nb_threads)
        adapter = HTTPAdapter(
            max_retries=retries,
            pool_connections=pool_size,
            pool_maxsize=pool_size,
            pool_block=True,
        )
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
        }
        return session

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

    def _url(self, kind: str = "data", params: Optional[dict] = None) -> Optional[str]:
        """Generate export API URL with QueryStrings if params.

        Args:
            params (dict, optional): dict of querystring parameters. Defaults to None.

        Returns:
            str: export API URL.
        """
        if kind == "data":
            if self._config.data_export_id is None:
                return None
            url = (
                f"{self._api_url}{self._export_api_path}/api/"
                f"{str(self._config.data_export_id)}"
            )
        elif kind == "metadata":
            if self._config.metadata_export_id is None:
                return None
            url = (
                f"{self._api_url}{self._export_api_path}/api/"
                f"{str(self._config.metadata_export_id)}"
            )
        elif kind == "log":
            url = f"{self._api_url}synthese/log"
        else:
            return None
        if params is not None:
            logger.debug("params %s", params)
            # The synthese log endpoint accepts repeated parameters (notably
            # the lower and upper bounds of meta_last_action_date).
            url = url + "?" + urlencode(params, doseq=kind == "log")
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
        # Check kind value
        if self._url(kind) is None:
            return None, 0, None

        api_url = self._url(kind, params)
        response = self._session.get(url=api_url, timeout=self._timeout)
        response.raise_for_status()
        total_filtered, limit = self._pagination_values(response, api_url)
        total_pages = math.ceil(total_filtered / limit)
        logger.debug(
            _("API %(url)s contains %(count)s data in %(pages)s page(s)"),
            {"url": api_url, "count": total_filtered, "pages": total_pages},
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
            return page_list, total_filtered, response.status_code

        return None, 0, response.status_code

    @staticmethod
    def _pagination_values(response, api_url: str) -> tuple[int, int]:
        """Validate a pagination response and return its total and limit."""
        try:
            payload = response.json()
        except ValueError as error:
            raise APIException(f"Invalid JSON response from {api_url}") from error
        if not isinstance(payload, dict):
            raise APIException(f"Invalid API response from {api_url}: expected an object")
        try:
            total = payload["total_filtered"] if "total_filtered" in payload else payload["total"]
            limit = payload["limit"]
            if not isinstance(total, int) or not isinstance(limit, int) or limit <= 0:
                raise TypeError
        except (KeyError, TypeError) as error:
            raise APIException(
                f"Invalid pagination response from {api_url}: missing or invalid total/limit"
            ) from error
        return total, limit

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
            page_request = session.get(url=page_url, timeout=self._timeout)
            self._http_status = page_request.status_code
            page_request.raise_for_status()
            try:
                resp = page_request.json()
            except ValueError as error:
                raise APIException(f"Invalid JSON response from {page_url}") from error
            if not isinstance(resp, dict) or not isinstance(resp.get("items"), list):
                raise APIException(f"Invalid API response from {page_url}: 'items' must be a list")
            return resp
        except RequestException:
            self._transfer_errors += 1
            logger.exception(_("Download data from %s failed"), page_url)
            raise
        except APIException as error:
            logger.critical(_("Download data from %s failed"), page_url)
            logger.critical(str(error))
            raise

    def get_cursor_page(self, params: dict) -> dict:
        """Get one data page using caller-provided keyset pagination filters."""
        page_url = self._url("data", params)
        if page_url is None:
            raise APIException("The data export URL is not configured")
        return self.get_page(page_url)


class DataAPI(BaseAPI):
    """Data API"""

    def __init__(self, config):
        super().__init__(config, "data")

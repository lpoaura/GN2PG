import math
import re
from types import SimpleNamespace
from urllib.parse import urlencode

import pytest
from requests.exceptions import HTTPError

from gn2pg.api import APIException, BaseAPI


class TestApi:
    def test_base_api_url(self, gn2pg_conf_one_source):
        url = re.sub(r"/$", "", gn2pg_conf_one_source._source.url)
        gn2pg_conf_one_source._source.url = url

        base_api = BaseAPI(config=gn2pg_conf_one_source, controler=None)

        assert base_api._api_url.endswith("/")

    def test_data_export_url(self):
        base_api = object.__new__(BaseAPI)
        base_api._api_url = "https://geonature.example/api/"
        base_api._export_api_path = "exports"
        base_api._config = SimpleNamespace(data_export_id=17)

        assert base_api._url() == "https://geonature.example/api/exports/api/17"

    def test_metadata_export_url(self):
        base_api = object.__new__(BaseAPI)
        base_api._api_url = "https://geonature.example/api/"
        base_api._export_api_path = "exports"
        base_api._config = SimpleNamespace(metadata_export_id=23)

        assert base_api._url(kind="metadata") == "https://geonature.example/api/exports/api/23"

    def test_log_url_encodes_repeated_date_bounds(self):
        base_api = object.__new__(BaseAPI)
        base_api._api_url = "https://geonature.example/api/"

        url = base_api._url(
            kind="log",
            params={
                "meta_last_action_date": ["gte:2026-08-01", "lte:2026-08-27"],
                "sort": "meta_last_action_date:asc",
            },
        )

        assert url.count("meta_last_action_date=") == 2
        assert "sort=meta_last_action_date%3Aasc" in url

    def test_page_list(self, base_api):
        params = {"limit": 10}
        api_url = base_api._url(params=params)
        r = base_api._session.get(url=api_url)
        resp = r.json()
        limit = resp["limit"]

        page_list, total_filtered, status_code = base_api.page_list(params=params)
        total_pages = math.ceil(total_filtered / limit)

        assert len(page_list) == total_pages
        for i, page in enumerate(page_list):
            assert urlencode(params) in page
            assert f"offset={i}" in page

    def test_get_page_uses_timeout_and_validates_items(self):
        class Response:
            status_code = 200

            @staticmethod
            def raise_for_status():
                return None

            @staticmethod
            def json():
                return {"items": []}

        class Session:
            def __init__(self):
                self.call = None

            def get(self, **kwargs):
                self.call = kwargs
                return Response()

        api = object.__new__(BaseAPI)
        api._session = Session()
        api._timeout = (3, 12)
        api._http_status = 0
        api._transfer_errors = 0

        assert api.get_page("https://example.test/page") == {"items": []}
        assert api._session.call["timeout"] == (3, 12)

    def test_get_page_rejects_invalid_json_shape(self):
        response = SimpleNamespace(
            status_code=200,
            raise_for_status=lambda: None,
            json=lambda: {"total": 1},
        )
        api = object.__new__(BaseAPI)
        api._session = SimpleNamespace(get=lambda **kwargs: response)
        api._timeout = (3, 12)
        api._http_status = 0
        api._transfer_errors = 0

        with pytest.raises(APIException, match="items"):
            api.get_page("https://example.test/page")

    def test_page_list_raises_on_http_error(self):
        response = SimpleNamespace(
            status_code=503,
            raise_for_status=lambda: (_ for _ in ()).throw(HTTPError("unavailable")),
        )
        api = object.__new__(BaseAPI)
        api._session = SimpleNamespace(get=lambda **kwargs: response)
        api._timeout = (3, 12)
        api._url = lambda kind="data", params=None: "https://example.test/export"

        with pytest.raises(HTTPError, match="unavailable"):
            api.page_list(params={"limit": 100})

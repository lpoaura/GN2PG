import math
import re
from urllib.parse import urlencode

from gn2pg.api import BaseAPI


class TestApi:
    def test_base_api_url(self, gn2pg_conf_one_source):
        url = re.sub(r"/$", "", gn2pg_conf_one_source._source.url)
        gn2pg_conf_one_source._source.url = url

        base_api = BaseAPI(config=gn2pg_conf_one_source, controler=None)

        assert base_api._api_url.endswith("/")

    def test_page_list(self, base_api):
        params = {"limit": 10}
        api_url = base_api._url(params=params)
        r = base_api._session.get(url=api_url)
        resp = r.json()
        total_filtered = resp["total_filtered"]
        total_pages = math.ceil(total_filtered / params.get("limit"))

        page_gen = base_api._page_list(params=params)

        page_list = list(page_gen)
        assert len(page_list) == total_pages
        for i, page in enumerate(page_list):
            assert urlencode(params) in page
            assert f"offset={i}" in page

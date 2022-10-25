import math
from urllib.parse import urlencode


class TestApi:
    def test_page_list(self, base_api):
        params = [("limit", 10)]
        api_url = base_api._url(params=params)
        r = base_api._session.get(url=api_url)
        resp = r.json()
        total_filtered = resp["total_filtered"]
        total_pages = math.ceil(total_filtered / params[0][1])

        page_gen = base_api._page_list(params=params)

        page_list = list(page_gen)
        assert len(page_list) == total_pages
        assert all(urlencode(params) in page for page in page_list)

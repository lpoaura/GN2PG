import pytest

from gn2pg.api import BaseAPI


@pytest.fixture
def base_api(gn2pg_conf_one_source):
    return BaseAPI(config=gn2pg_conf_one_source, controler=None)

import pytest

from gn2pg.api import BaseAPI


@pytest.fixture
def base_api(gn2pg_conf):
    cfg_source_list = gn2pg_conf.source_list
    cfg = list(cfg_source_list.values())[0]
    return BaseAPI(config=cfg, controler=None)

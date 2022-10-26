import pytest

from gn2pg.download import Data

@pytest.fixture
def data(gn2pg_conf_one_source, store_postgresql):
    return Data(config=gn2pg_conf_one_source, backend=store_postgresql)
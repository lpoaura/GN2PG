import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy_utils import create_database, database_exists, drop_database

from gn2pg.store_postgresql import db_url


@pytest.fixture(scope="session", autouse=True)
def db(gn2pg_conf_one_source):
    engine = create_engine(URL.create(**db_url(gn2pg_conf_one_source)))
    if not database_exists(engine.url):
        create_database(engine.url)
    yield
    drop_database(engine.url)

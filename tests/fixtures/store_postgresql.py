import pytest

from gn2pg.store_postgresql import PostgresqlUtils, StorePostgresql


@pytest.fixture(scope="session")
def postgresql_utils(gn2pg_conf_one_source):
    utils = PostgresqlUtils(config=gn2pg_conf_one_source)
    utils.create_json_tables()
    return utils
    
@pytest.fixture
def store_postgresql(gn2pg_conf_one_source, postgresql_utils):
    with StorePostgresql(gn2pg_conf_one_source) as store_pg:
        yield store_pg
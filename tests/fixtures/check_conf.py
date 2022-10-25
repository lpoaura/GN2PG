import tempfile

import pytest

from gn2pg.check_conf import Gn2PgConf
from gn2pg.env import ENVDIR


@pytest.fixture
def toml_conf(pytestconfig):
    user = pytestconfig.getoption("user")
    password = pytestconfig.getoption("password")
    url = pytestconfig.getoption("url")
    toml_str = f"""
    [db]
    db_host = "localhost"
    db_port = 5432
    db_user = "<dbUser>"
    db_password = "<dbPassword>"
    db_name = "<dbName>"
    db_schema_import = "gn2pg_import"
        # Additional connection options (optional)
        [db.db_querystring]
        sslmode = "prefer"


    # Source configuration,
    # Ducplicate this block for each source (1 source = 1 export)
    [[source]]
    # Source name, will be use to tag stored data in import table
    name = "Source1"
    # use false to disable source
    #enable= true
    # GeoNature source login
    user_name = "{user}"
    # GeoNature source password
    user_password = "{password}"
    # GeoNature source URL
    url = "{url}"
    # GeoNature source Export id
    export_id = 1
    # Data type (used to distinct datas and to conditionning triggers)
    data_type = "synthese_with_metadata"

    [tuning]
    # Max retries of API calls before aborting.
    max_retry = 5
    # Maximum number of API requests, for debugging only.
    # - 0 means unlimited
    # - >0 limit number of API requests
    max_requests = 0
    """

    return toml_str


@pytest.fixture
def gn2pg_conf_file(toml_conf):
    with tempfile.NamedTemporaryFile(
        dir=ENVDIR, suffix=".toml", delete=True, mode="w"
    ) as f:
        name = f.name
        f.write(toml_conf)
        f.seek(0)
        yield name


@pytest.fixture
def gn2pg_conf(gn2pg_conf_file):
    return Gn2PgConf(file=gn2pg_conf_file)

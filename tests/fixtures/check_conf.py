import tempfile

import pytest

from gn2pg.check_conf import Gn2PgConf
from gn2pg.env import ENVDIR


@pytest.fixture(scope="session")
def toml_conf(pytestconfig):
    user = pytestconfig.getoption("user")
    password = pytestconfig.getoption("password")
    url = pytestconfig.getoption("url")
    db_user = pytestconfig.getoption("db_user")
    db_password = pytestconfig.getoption("db_password")
    db_port = int(pytestconfig.getoption("db_port"))
    db_name = pytestconfig.getoption("db_name")
    export_id = pytestconfig.getoption("export_id")
    nb_threads = pytestconfig.getoption("nb_threads")
    toml_str = f"""
    [db]
    db_host = "localhost"
    db_port = {db_port}
    db_user = "{db_user}"
    db_password = "{db_password}"
    db_name = "{db_name}"
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
    export_id = {export_id}
    # Data type (used to distinct datas and to conditionning triggers)
    data_type = "synthese_with_metadata"

    [tuning]
    # Max retries of API calls before aborting.
    max_retry = 5
    # Maximum number of API requests, for debugging only.
    # - 0 means unlimited
    # - >0 limit number of API requests
    max_requests = 0
    # Number of computing threads
    nb_threads = {nb_threads}
    """

    return toml_str


@pytest.fixture(scope="session")
def gn2pg_conf_file(toml_conf):
    with tempfile.NamedTemporaryFile(dir=ENVDIR, suffix=".toml", delete=True, mode="w") as f:
        name = f.name
        f.write(toml_conf)
        f.seek(0)
        yield name


@pytest.fixture(scope="session")
def gn2pg_conf(gn2pg_conf_file):
    return Gn2PgConf(file=gn2pg_conf_file)


@pytest.fixture(scope="session")
def gn2pg_conf_one_source(gn2pg_conf):
    cfg_source_list = gn2pg_conf.source_list
    return list(cfg_source_list.values())[0]

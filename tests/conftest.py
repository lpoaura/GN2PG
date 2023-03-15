from tests.fixtures.app import *
from tests.fixtures.app import  _session,app

def pytest_addoption(parser):
    parser.addoption("--user", action="store", default="default user")
    parser.addoption("--password", action="store", default="default password")
    parser.addoption("--url", action="store", default="default url")
    parser.addoption("--db-user", action="store", default="dbuser")
    parser.addoption("--db-password", action="store", default="dbpwd")
    parser.addoption("--db-port", action="store", default=5432)
    parser.addoption("--db-name", action="store", default="testgn2pg_test")
    parser.addoption("--export-id", action="store", default=1)
    parser.addoption("--nb-threads", action="store", default=1)


pytest_plugins = [
    "tests.fixtures.api",
    "tests.fixtures.check_conf",
    "tests.fixtures.db",
    "tests.fixtures.download",
    "tests.fixtures.store_postgresql",
]

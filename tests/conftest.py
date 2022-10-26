def pytest_addoption(parser):
    parser.addoption("--user", action="store", default="default user")
    parser.addoption("--password", action="store", default="default password")
    parser.addoption("--url", action="store", default="default url")
    parser.addoption("--db-user", action="store", default="dbuser")
    parser.addoption("--db-password", action="store", default="dbpwd")
    parser.addoption("--db-port", action="store", default=5432)
    parser.addoption("--db-name", action="store",default="testgn2pg_test")


pytest_plugins = ["tests.fixtures.api", "tests.fixtures.check_conf", "tests.fixtures.db"]

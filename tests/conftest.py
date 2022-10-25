def pytest_addoption(parser):
    parser.addoption("--user", action="store", default="default user")
    parser.addoption("--password", action="store", default="default password")
    parser.addoption("--url", action="store", default="default url")


pytest_plugins = ["tests.fixtures.api", "tests.fixtures.check_conf"]

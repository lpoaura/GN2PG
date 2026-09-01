import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from gn2pg.store_postgresql import db_url


@pytest.fixture(scope="session")
def db(gn2pg_conf_one_source):
    database_url = URL.create(**db_url(gn2pg_conf_one_source))
    database_name = database_url.database
    if not database_name or database_name == "postgres":
        raise ValueError("The test database must have a dedicated name")

    admin_engine = create_engine(
        database_url.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
    )
    quoted_database_name = admin_engine.dialect.identifier_preparer.quote(database_name)

    with admin_engine.connect() as connection:
        exists = connection.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :database_name"),
            {"database_name": database_name},
        ).scalar()
        if not exists:
            connection.exec_driver_sql(f"CREATE DATABASE {quoted_database_name}")

    try:
        yield
    finally:
        with admin_engine.connect() as connection:
            connection.execute(
                text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = :database_name AND pid <> pg_backend_pid()"
                ),
                {"database_name": database_name},
            )
            connection.exec_driver_sql(f"DROP DATABASE IF EXISTS {quoted_database_name}")
        admin_engine.dispose()

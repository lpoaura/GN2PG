#!/usr/bin/env python
"""Generate an Alembic revision from the shared GN2PG table definitions."""

import argparse

from alembic import command
from sqlalchemy.engine import URL

from gn2pg.check_conf import Gn2PgConf
from gn2pg.database.migrations import alembic_config, database_status
from gn2pg.store_postgresql import db_url


def arguments() -> argparse.Namespace:
    """Parse developer-facing revision generation arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="GN2PG TOML configuration file")
    parser.add_argument("--message", required=True, help="Alembic revision message")
    return parser.parse_args()


def main() -> None:
    """Validate the database state and autogenerate a revision."""
    args = arguments()
    configuration = Gn2PgConf(args.config)
    source = next(iter(configuration.source_list.values()))
    url = URL.create(**db_url(source))
    schema = source.database.schema_import
    status = database_status(url, schema)
    if status.current != status.head:
        raise SystemExit(
            f"Database must be at head before autogeneration "
            f"(current={status.current or 'none'}, head={status.head})"
        )

    command.revision(
        alembic_config(url, schema),
        message=args.message,
        autogenerate=True,
    )


if __name__ == "__main__":
    main()

"""Alembic environment for GN2PG's configurable import schema."""

# Alembic exposes context operations dynamically at migration runtime.
# pylint: disable=no-member

from alembic import context
from sqlalchemy import engine_from_config, pool, text
from sqlalchemy.dialects import postgresql

from gn2pg.database import build_metadata

config = context.config
schema = config.attributes.get("schema", "gn2pg_import")
target_metadata = build_metadata(schema)


def include_name(name, object_type, parent_names) -> bool:
    """Restrict reflection to the configured GN2PG schema."""
    if object_type == "schema":
        return name == schema
    if object_type == "table":
        return parent_names.get("schema_name") == schema
    return True


def run_migrations_offline() -> None:
    """Run migrations without creating an Engine."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
        include_name=include_name,
        version_table="alembic_version",
        version_table_schema=schema,
        schema=schema,
    )
    quoted_schema = postgresql.dialect().identifier_preparer.quote(schema)
    context.execute(f"CREATE SCHEMA IF NOT EXISTS {quoted_schema}")
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations with a live database connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        quoted_schema = connection.dialect.identifier_preparer.quote(schema)
        connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {quoted_schema}"))
        connection.commit()
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_name=include_name,
            version_table="alembic_version",
            version_table_schema=schema,
            schema=schema,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

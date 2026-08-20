"""Programmatic Alembic integration for the GN2PG CLI."""

from dataclasses import dataclass
from importlib.resources import as_file, files

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import URL
from sqlalchemy.schema import PrimaryKeyConstraint, UniqueConstraint

from gn2pg.database.tables import build_metadata

BASELINE_REVISION = "20260818_01"
VERSION_TABLE = "alembic_version"


class ExistingSchemaError(RuntimeError):
    """The existing database cannot safely be stamped as the GN2PG baseline."""


@dataclass(frozen=True)
class DatabaseStatus:
    """Current state of the GN2PG Alembic history."""

    current: str | None
    head: str
    has_version_table: bool
    existing_tables: frozenset[str]

    @property
    def pending(self) -> bool:
        """Return whether the database is behind the migration head."""
        return self.current != self.head


def alembic_config(url: URL, schema: str) -> Config:
    """Build an Alembic configuration from the application configuration."""
    migrations = files("gn2pg").joinpath("alembic")
    with as_file(migrations) as migration_path:
        config = Config()
        config.set_main_option("script_location", str(migration_path))
        config.set_main_option("sqlalchemy.url", url.render_as_string(hide_password=False))
        config.attributes["schema"] = schema
        return config


def database_status(url: URL, schema: str) -> DatabaseStatus:
    """Inspect the current and target migration revisions without changing the database."""
    config = alembic_config(url, schema)
    head = ScriptDirectory.from_config(config).get_current_head()
    if head is None:
        raise ExistingSchemaError("Alembic has no head revision")

    engine = create_engine(url)
    try:
        with engine.connect() as connection:
            inspector = inspect(connection)
            tables = frozenset(inspector.get_table_names(schema=schema))
            context = MigrationContext.configure(
                connection,
                opts={"version_table": VERSION_TABLE, "version_table_schema": schema},
            )
            current = context.get_current_revision() if VERSION_TABLE in tables else None
    finally:
        engine.dispose()

    return DatabaseStatus(
        current=current,
        head=head,
        has_version_table=VERSION_TABLE in tables,
        existing_tables=tables,
    )


def upgrade_database(url: URL, schema: str, revision: str = "head") -> None:
    """Upgrade a GN2PG database to an Alembic revision."""
    command.upgrade(alembic_config(url, schema), revision)


def stamp_existing_database(url: URL, schema: str) -> None:
    """Validate a legacy GN2PG schema and stamp it at the baseline revision."""
    status = database_status(url, schema)
    if status.has_version_table:
        # Check if alembic_version table exists
        raise ExistingSchemaError(
            f"{schema}.{VERSION_TABLE} already exists at revision {status.current or 'unknown'}"
        )

    errors = validate_existing_schema(url, schema)
    if errors:
        details = "\n - ".join(errors)
        raise ExistingSchemaError(
            f"Existing schema does not match the GN2PG baseline:\n - {details}"
        )

    command.stamp(alembic_config(url, schema), BASELINE_REVISION)


def validate_existing_schema(url: URL, schema: str) -> list[str]:
    """Return structural differences that make a baseline stamp unsafe."""
    expected_metadata = build_metadata(schema)
    expected_tables = {table.name: table for table in expected_metadata.sorted_tables}
    errors: list[str] = []
    engine = create_engine(url)
    try:
        with engine.connect() as connection:
            inspector = inspect(connection)
            actual_tables = set(inspector.get_table_names(schema=schema))
            missing_tables = set(expected_tables) - actual_tables
            if missing_tables:
                errors.append(f"missing tables: {', '.join(sorted(missing_tables))}")

            for name in sorted(set(expected_tables) & actual_tables):
                _validate_table(inspector, schema, expected_tables[name], errors)
    finally:
        engine.dispose()
    return errors


def _validate_table(inspector, schema: str, expected, errors: list[str]) -> None:
    """Compare columns and key constraints for one reflected table."""
    _validate_columns(inspector, schema, expected, errors)
    _validate_primary_and_unique_keys(inspector, schema, expected, errors)
    _validate_indexes(inspector, schema, expected, errors)
    _validate_foreign_keys(inspector, schema, expected, errors)


def _validate_columns(inspector, schema: str, expected, errors: list[str]) -> None:
    """Compare required column types and nullability."""
    actual_columns = {
        column["name"]: column for column in inspector.get_columns(expected.name, schema)
    }
    for column in expected.columns:
        actual = actual_columns.get(column.name)
        label = f"{expected.name}.{column.name}"
        if actual is None:
            errors.append(f"missing column: {label}")
            continue
        # SQLAlchemy exposes no public dialect-independent type-affinity comparison.
        if not column.type._compare_type_affinity(actual["type"]):  # pylint: disable=W0212
            errors.append(
                f"incompatible type: {label} ({actual['type']} instead of {column.type})"
            )
        if bool(actual["nullable"]) != bool(column.nullable):
            errors.append(f"incompatible nullability: {label}")


def _validate_primary_and_unique_keys(inspector, schema, expected, errors) -> None:
    """Compare primary and unique keys."""
    primary_key = next(
        constraint
        for constraint in expected.constraints
        if isinstance(constraint, PrimaryKeyConstraint)
    )
    actual_pk = inspector.get_pk_constraint(expected.name, schema).get("constrained_columns") or []
    if list(primary_key.columns.keys()) != actual_pk:
        errors.append(f"incompatible primary key: {expected.name}")

    expected_uniques = {
        frozenset(constraint.columns.keys())
        for constraint in expected.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    actual_uniques = {
        frozenset(constraint.get("column_names") or [])
        for constraint in inspector.get_unique_constraints(expected.name, schema)
    }
    missing_uniques = expected_uniques - actual_uniques
    if missing_uniques:
        errors.append(f"missing unique constraints: {expected.name}")


def _validate_indexes(inspector, schema, expected, errors) -> None:
    """Compare required index column sets."""
    expected_indexes = {frozenset(index.columns.keys()) for index in expected.indexes}
    actual_indexes = {
        frozenset(index.get("column_names") or [])
        for index in inspector.get_indexes(expected.name, schema)
    }
    if expected_indexes - actual_indexes:
        errors.append(f"missing indexes: {expected.name}")


def _validate_foreign_keys(inspector, schema, expected, errors) -> None:
    """Compare required foreign-key targets."""
    expected_foreign_keys = {
        (
            tuple(constraint.column_keys),
            tuple(element.target_fullname for element in constraint.elements),
        )
        for constraint in expected.foreign_key_constraints
    }
    actual_foreign_keys = {
        (
            tuple(constraint.get("constrained_columns") or []),
            tuple(
                f"{constraint.get('referred_schema') or schema}."
                f"{constraint.get('referred_table')}.{column}"
                for column in constraint.get("referred_columns") or []
            ),
        )
        for constraint in inspector.get_foreign_keys(expected.name, schema)
    }
    if expected_foreign_keys - actual_foreign_keys:
        errors.append(f"missing foreign keys: {expected.name}")

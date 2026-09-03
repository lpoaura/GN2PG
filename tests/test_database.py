"""Tests for the shared schema and Alembic configuration."""

from io import StringIO

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy.engine import make_url

from gn2pg.database import build_metadata, migrations


def test_shared_metadata_contains_all_tables_for_configured_schema():
    """Table definitions are shared and qualified with the requested schema."""
    metadata = build_metadata("custom_import")

    assert set(metadata.tables) == {
        "custom_import.import_log",
        "custom_import.error_log",
        "custom_import.data_json",
        "custom_import.metadata_json",
    }
    assert "test" not in metadata.tables["custom_import.import_log"].c
    assert build_metadata("custom_import") is metadata


def test_alembic_has_a_single_initial_head():
    """The migration history exposes one current head."""
    config = Config()
    config.set_main_option("script_location", "gn2pg/alembic")

    assert ScriptDirectory.from_config(config).get_heads() == ["20260903_03"]


def test_data_primary_key_uses_business_identity():
    data_table = build_metadata("custom_import").tables["custom_import.data_json"]

    assert list(data_table.primary_key.columns.keys()) == ["id_data", "controler", "source"]


def test_alembic_version_table_uses_project_schema():
    """Alembic stores its version in the same schema as GN2PG tables."""
    output = StringIO()
    config = Config(output_buffer=output)
    config.set_main_option("script_location", "gn2pg/alembic")
    config.set_main_option("sqlalchemy.url", "postgresql+psycopg2://user:pass@localhost/db")
    config.attributes["schema"] = "custom_import"

    command.upgrade(config, "head", sql=True)

    assert "CREATE TABLE custom_import.alembic_version" in output.getvalue()


def test_stamp_existing_targets_baseline_after_validation(monkeypatch):
    """A valid legacy schema is stamped at the baseline, never at head."""
    status = migrations.DatabaseStatus(
        current=None,
        head="future_head",
        has_version_table=False,
        existing_tables=frozenset({"import_log", "error_log", "data_json", "metadata_json"}),
    )
    monkeypatch.setattr(migrations, "database_status", lambda url, schema: status)
    monkeypatch.setattr(migrations, "validate_existing_schema", lambda url, schema: [])
    stamped = []
    monkeypatch.setattr(
        migrations.command,
        "stamp",
        lambda config, revision: stamped.append(revision),
    )

    migrations.stamp_existing_database(make_url("postgresql://"), "custom_import")

    assert stamped == [migrations.BASELINE_REVISION]


def test_stamp_existing_refuses_an_already_versioned_schema(monkeypatch):
    """An existing Alembic history is never overwritten by the legacy transition."""
    status = migrations.DatabaseStatus(
        current="some_revision",
        head="some_revision",
        has_version_table=True,
        existing_tables=frozenset({"alembic_version"}),
    )
    monkeypatch.setattr(migrations, "database_status", lambda url, schema: status)

    with pytest.raises(migrations.ExistingSchemaError):
        migrations.stamp_existing_database(make_url("postgresql://"), "custom_import")

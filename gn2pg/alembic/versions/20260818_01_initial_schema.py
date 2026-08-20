"""Create the initial GN2PG import schema.

Revision ID: 20260818_01
Revises: None
"""

# pylint: disable=invalid-name,no-member

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260818_01"
down_revision = None
branch_labels = None
depends_on = None


def _schema() -> str:
    return op.get_context().opts.get("schema", "gn2pg_import")


def _index(schema: str, table: str, column: str) -> str:
    return f"ix_{schema}_{table}_{column}"


def upgrade() -> None:
    """Create extensions and an immutable snapshot of the initial schema."""
    schema = _schema()
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.create_table(
        "import_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("controler", sa.String(), nullable=False),
        sa.Column("xfer_type", sa.String(), nullable=True),
        sa.Column("xfer_status", sa.String(), nullable=True),
        sa.Column("xfer_start_ts", sa.DateTime(), nullable=False),
        sa.Column("xfer_end_ts", sa.DateTime(), nullable=True),
        sa.Column("api_count_items", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("api_count_errors", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("data_count_upserts", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("data_count_delete", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("data_count_errors", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "metadata_count_upserts", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "metadata_count_errors", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column(
            "xfer_filters",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema=schema,
    )
    op.create_index(
        _index(schema, "import_log", "source"), "import_log", ["source"], schema=schema
    )
    op.create_index(
        _index(schema, "import_log", "xfer_type"), "import_log", ["xfer_type"], schema=schema
    )
    op.create_table(
        "error_log",
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("uuid", postgresql.UUID(), nullable=False),
        sa.Column("controler", sa.String(), nullable=False),
        sa.Column("last_ts", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("item", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error", sa.String(), nullable=True),
        sa.Column("import_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["import_id"],
            [f"{schema}.import_log.id"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        schema=schema,
    )
    op.create_index(
        _index(schema, "error_log", "import_id"), "error_log", ["import_id"], schema=schema
    )
    op.create_index(_index(schema, "error_log", "uuid"), "error_log", ["uuid"], schema=schema)
    op.create_table(
        "data_json",
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("controler", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("id_data", sa.Integer(), nullable=False),
        sa.Column("uuid", postgresql.UUID(), nullable=True),
        sa.Column("item", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("update_ts", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("import_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["import_id"], [f"{schema}.import_log.id"], onupdate="CASCADE"),
        sa.PrimaryKeyConstraint("id_data", "source", "type", name="pk_source_data"),
        sa.UniqueConstraint("uuid", name="unique_uuid"),
        schema=schema,
    )
    op.create_index(
        _index(schema, "data_json", "id_data"), "data_json", ["id_data"], schema=schema
    )
    op.create_index(_index(schema, "data_json", "uuid"), "data_json", ["uuid"], schema=schema)
    op.create_table(
        "metadata_json",
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("controler", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("level", sa.String(), nullable=False),
        sa.Column("uuid", postgresql.UUID(), nullable=False),
        sa.Column("item", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("update_ts", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("import_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["import_id"], [f"{schema}.import_log.id"], onupdate="CASCADE"),
        sa.PrimaryKeyConstraint("uuid", "source", name="pk_source_metadata"),
        sa.UniqueConstraint("uuid", name="metadata_unique_uuid"),
        schema=schema,
    )
    op.create_index(
        _index(schema, "metadata_json", "uuid"), "metadata_json", ["uuid"], schema=schema
    )


def downgrade() -> None:
    """Drop GN2PG tables while preserving the schema and shared extensions."""
    schema = _schema()
    op.drop_table("metadata_json", schema=schema)
    op.drop_table("data_json", schema=schema)
    op.drop_table("error_log", schema=schema)
    op.drop_table("import_log", schema=schema)

"""Use the data business key as the primary key.

Revision ID: 20260903_03
Revises: 20260902_02
"""

# Alembic requires lowercase revision attributes and exposes operations dynamically.
# pylint: disable=invalid-name,no-member

from alembic import op

revision = "20260903_03"
down_revision = "20260902_02"
branch_labels = None
depends_on = None


def _schema() -> str:
    return op.get_context().opts.get("schema", "gn2pg_import")


def upgrade() -> None:
    """Replace the format-dependent key with the data business key."""
    schema = _schema()
    op.drop_constraint("pk_source_data", "data_json", schema=schema, type_="primary")
    op.create_primary_key(
        "pk_source_data",
        "data_json",
        ["id_data", "controler", "source"],
        schema=schema,
    )


def downgrade() -> None:
    """Restore the former format-dependent primary key."""
    schema = _schema()
    op.drop_constraint("pk_source_data", "data_json", schema=schema, type_="primary")
    op.create_primary_key(
        "pk_source_data",
        "data_json",
        ["id_data", "source", "type"],
        schema=schema,
    )

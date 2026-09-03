"""Add not nullable constraint on import_id fk

Revision ID: aced35dc4d9e
Revises: 20260818_01
Create Date: 2026-09-02 15:58:35.711342
"""

# Alembic requires lowercase revision attributes and exposes operations dynamically.
# pylint: disable=invalid-name,no-member

from typing import Optional, Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260902_02"
down_revision: Optional[str] = "20260818_01"
branch_labels: Optional[Union[str, Sequence[str]]] = None
depends_on: Optional[Union[str, Sequence[str]]] = None


def _schema() -> str:
    return op.get_context().opts.get("schema", "gn2pg_import")


def _index(schema: str, table: str, column: str) -> str:
    return f"ix_{schema}_{table}_{column}"


def upgrade() -> None:
    """Make import identifiers mandatory on imported records and errors."""
    schema = _schema()
    op.alter_column(
        "data_json", "import_id", existing_type=sa.INTEGER(), nullable=False, schema=schema
    )
    op.alter_column(
        "error_log", "import_id", existing_type=sa.INTEGER(), nullable=False, schema=schema
    )
    op.alter_column(
        "metadata_json", "import_id", existing_type=sa.INTEGER(), nullable=False, schema=schema
    )


def downgrade() -> None:
    """Allow imported records and errors without an import identifier."""
    schema = _schema()
    op.alter_column(
        "metadata_json", "import_id", existing_type=sa.INTEGER(), nullable=True, schema=schema
    )
    op.alter_column(
        "error_log", "import_id", existing_type=sa.INTEGER(), nullable=True, schema=schema
    )
    op.alter_column(
        "data_json", "import_id", existing_type=sa.INTEGER(), nullable=True, schema=schema
    )

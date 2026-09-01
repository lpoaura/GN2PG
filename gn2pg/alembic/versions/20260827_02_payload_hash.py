"""Add a generated hash for detecting unchanged data payloads.

Revision ID: 20260827_02
Revises: 20260827_01
"""

# pylint: disable=invalid-name,no-member

import sqlalchemy as sa
from alembic import op

revision = "20260827_02"
down_revision = "20260827_01"
branch_labels = None
depends_on = None


def _schema() -> str:
    return op.get_context().opts.get("schema", "gn2pg_import")


def upgrade() -> None:
    """Add the SHA-256 generated from the canonical JSONB text."""
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.add_column(
        "data_json",
        sa.Column(
            "payload_hash",
            sa.LargeBinary(),
            sa.Computed("digest(item::text, 'sha256')", persisted=True),
            nullable=False,
        ),
        schema=_schema(),
    )


def downgrade() -> None:
    """Remove the generated payload hash."""
    op.drop_column("data_json", "payload_hash", schema=_schema())

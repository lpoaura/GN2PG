"""Add durable page checkpoints for resumable transfers.

Revision ID: 20260827_01
Revises: 20260818_01
"""

# pylint: disable=invalid-name,no-member

import sqlalchemy as sa
from alembic import op

revision = "20260827_01"
down_revision = "20260818_01"
branch_labels = None
depends_on = None


def _schema() -> str:
    return op.get_context().opts.get("schema", "gn2pg_import")


def upgrade() -> None:
    """Create the durable page checkpoint table."""
    schema = _schema()
    op.add_column("import_log", sa.Column("cursor_phase", sa.String()), schema=schema)
    op.add_column("import_log", sa.Column("cursor_column", sa.String()), schema=schema)
    op.add_column("import_log", sa.Column("cursor_value", sa.BigInteger()), schema=schema)
    op.create_table(
        "download_page",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("import_id", sa.Integer(), nullable=False),
        sa.Column("phase", sa.String(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("attempts", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("item_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["import_id"], [f"{schema}.import_log.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("import_id", "phase", "page_number", name="uq_download_page"),
        schema=schema,
    )
    op.create_index(
        f"ix_{schema}_download_page_import_id",
        "download_page",
        ["import_id"],
        schema=schema,
    )


def downgrade() -> None:
    """Drop the durable page checkpoint table."""
    schema = _schema()
    op.drop_table("download_page", schema=schema)
    op.drop_column("import_log", "cursor_value", schema=schema)
    op.drop_column("import_log", "cursor_column", schema=schema)
    op.drop_column("import_log", "cursor_phase", schema=schema)

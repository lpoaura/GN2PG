"""Canonical definitions of the tables managed by GN2PG."""

from functools import lru_cache

from sqlalchemy import (
    BigInteger,
    Column,
    Computed,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    MetaData,
    PrimaryKeyConstraint,
    String,
    Table,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID


@lru_cache(maxsize=None)
def build_metadata(schema: str = "gn2pg_import") -> MetaData:
    """Build and cache the GN2PG table definitions for one PostgreSQL schema."""
    metadata = MetaData(schema=schema)

    Table(
        "import_log",
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("source", String, nullable=False, index=True),
        Column("controler", String, nullable=False),
        Column("xfer_type", String, index=True),
        Column("xfer_status", String),
        Column("xfer_start_ts", DateTime, nullable=False),
        Column("xfer_end_ts", DateTime),
        Column("api_count_items", Integer, nullable=False, server_default=text("0")),
        Column("api_count_errors", Integer, nullable=False, server_default=text("0")),
        Column("data_count_upserts", Integer, nullable=False, server_default=text("0")),
        Column("data_count_delete", Integer, nullable=False, server_default=text("0")),
        Column("data_count_errors", Integer, nullable=False, server_default=text("0")),
        Column("metadata_count_upserts", Integer, nullable=False, server_default=text("0")),
        Column("metadata_count_errors", Integer, nullable=False, server_default=text("0")),
        Column("xfer_filters", JSONB, server_default=text("'{}'::jsonb")),
        Column("comment", Text),
        Column("cursor_phase", String),
        Column("cursor_column", String),
        Column("cursor_value", BigInteger),
    )

    Table(
        "error_log",
        metadata,
        Column("source", String, nullable=False),
        Column("uuid", UUID, nullable=False, index=True),
        Column("controler", String, nullable=False),
        Column("last_ts", DateTime, server_default=text("now()"), nullable=False),
        Column("item", JSONB),
        Column("error", String),
        Column(
            "import_id",
            Integer,
            ForeignKey(f"{schema}.import_log.id", ondelete="CASCADE", onupdate="CASCADE"),
            index=True,
        ),
    )

    Table(
        "download_page",
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column(
            "import_id",
            Integer,
            ForeignKey(f"{schema}.import_log.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        Column("phase", String, nullable=False),
        Column("page_number", Integer, nullable=False),
        Column("url", Text, nullable=False),
        Column("status", String, nullable=False, server_default=text("'pending'")),
        Column("attempts", Integer, nullable=False, server_default=text("0")),
        Column("item_count", Integer, nullable=False, server_default=text("0")),
        Column("last_error", Text),
        Column("started_at", DateTime),
        Column("completed_at", DateTime),
        UniqueConstraint("import_id", "phase", "page_number", name="uq_download_page"),
    )

    Table(
        "data_json",
        metadata,
        Column("source", String, nullable=False),
        Column("controler", String, nullable=False),
        Column("type", String, nullable=False),
        Column("id_data", Integer, nullable=False, index=True),
        Column("uuid", UUID, index=True),
        Column("item", JSONB, nullable=False),
        Column(
            "payload_hash",
            LargeBinary,
            Computed("digest(item::text, 'sha256')", persisted=True),
            nullable=False,
        ),
        Column("update_ts", DateTime, server_default=text("now()"), nullable=False),
        Column(
            "import_id",
            Integer,
            ForeignKey(f"{schema}.import_log.id", onupdate="CASCADE"),
        ),
        PrimaryKeyConstraint("id_data", "source", "type", name="pk_source_data"),
        UniqueConstraint("uuid", name="unique_uuid"),
    )

    Table(
        "metadata_json",
        metadata,
        Column("source", String, nullable=False),
        Column("controler", String, nullable=False),
        Column("type", String, nullable=False),
        Column("level", String, nullable=False),
        Column("uuid", UUID, index=True),
        Column("item", JSONB, nullable=False),
        Column("update_ts", DateTime, server_default=text("now()"), nullable=False),
        Column(
            "import_id",
            Integer,
            ForeignKey(f"{schema}.import_log.id", onupdate="CASCADE"),
        ),
        PrimaryKeyConstraint("uuid", "source", name="pk_source_metadata"),
        UniqueConstraint("uuid", name="metadata_unique_uuid"),
    )

    return metadata

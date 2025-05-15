"""Module providing Models according to database from config file."""

from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from gn2pg.app.database import db


class ImportLog(db.Model):
    """Download logs table"""

    __tablename__ = "import_log"
    __table_args__ = {"schema": "gn2pg_import"}
    id = db.Column(db.Integer, db.Sequence("import_id_seq"), primary_key=True)
    source = db.Column(db.String, nullable=False, index=True)
    controler = db.Column(
        db.String,
        nullable=False,
    )
    xfer_type = db.Column(db.String, index=True)
    xfer_status = db.Column(db.String, index=True)
    xfer_http_status = db.Column(db.String, index=True)
    xfer_filters = db.Column(JSONB, server_default="{}")
    xfer_start_ts = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
    )
    xfer_end_ts = db.Column(
        db.DateTime(timezone=True),
        nullable=True,
    )
    # api_count_data = db.Column(db.Integer, index=True, nullable=False)
    api_count_errors = db.Column(db.Integer, nullable=False)
    data_count_upserts = db.Column(db.Integer, index=True, nullable=False)
    data_count_delete = db.Column(db.Integer, index=True, nullable=False)
    data_count_errors = db.Column(db.Integer, index=True)
    metadata_count_upserts = db.Column(db.Integer, index=True)
    metadata_count_errors = db.Column(db.Integer, index=True)
    comment = db.Column(db.String)

    def __repr__(self):
        return f"<Import_Log {self.id} {self.name}>"


class ErrorLog(db.Model):
    """Error logs table"""

    __tablename__ = "error_log"
    __table_args__ = {"schema": "gn2pg_import"}
    source = db.Column(db.String, nullable=False, index=True, primary_key=True)
    uuid = db.Column(UUID, nullable=False, index=True)
    controler = db.Column(
        db.String,
        nullable=False,
    )
    last_ts = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    item = db.Column(JSONB)
    error = db.Column(db.String)
    import_id = db.Column(
        db.Integer,
        db.ForeignKey("gn2pg_import.import_log.id", ondelete="CASCADE", onupdate="CASCADE"),
    )

    def __repr__(self):
        return f"<error_log {self.name}>"

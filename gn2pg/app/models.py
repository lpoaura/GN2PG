"""Module providing Models according to database from config file."""

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from gn2pg.app.database import db


class DownloadLog(db.Model):
    """Download logs table"""

    __tablename__ = "download_log"
    __table_args__ = {"schema": "gn2pg_import"}
    source = db.Column(db.String, nullable=False, index=True, primary_key=True)
    controler = db.Column(
        db.String,
        nullable=False,
    )
    download_ts = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    error_count = db.Column(db.Integer, index=True)
    http_status = db.Column(db.String, index=True)
    comment = db.Column(db.String)

    def __repr__(self):
        return f"<Download_Log {self.name}>"


class IncrementLog(db.Model):
    """Increment logs table"""

    __tablename__ = "increment_log"
    __table_args__ = {"schema": "gn2pg_import"}
    source = db.Column(db.String, nullable=False, index=True, primary_key=True)
    controler = db.Column(
        db.String,
        nullable=False,
    )
    last_ts = db.Column(
        db.DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"<increment_Log {self.name}>"


class ErrorLog(db.Model):
    """Error logs table"""

    __tablename__ = "error_log"
    __table_args__ = {"schema": "gn2pg_import"}
    source = db.Column(db.String, nullable=False, index=True, primary_key=True)
    id_data = db.Column(db.String, nullable=False, index=True, primary_key=True)
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

    def __repr__(self):
        return f"<error_log {self.name}>"

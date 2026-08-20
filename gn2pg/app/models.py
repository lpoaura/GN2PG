"""Flask ORM mappings backed by the shared GN2PG table definitions."""

from gn2pg.app.config import FLASK_CONFIG
from gn2pg.app.database import db
from gn2pg.database import build_metadata

shared_metadata = build_metadata(FLASK_CONFIG.database["SCHEMA"])


class ImportLog(db.Model):
    """Download log."""

    __table__ = shared_metadata.tables[f"{shared_metadata.schema}.import_log"]

    def __repr__(self):
        return f"<ImportLog {self.id}>"


class ErrorLog(db.Model):
    """Error log mapped on the historical table without a database primary key."""

    __table__ = shared_metadata.tables[f"{shared_metadata.schema}.error_log"]
    __mapper_args__ = {
        "primary_key": [
            __table__.c.source,
            __table__.c.uuid,
            __table__.c.controler,
            __table__.c.import_id,
        ]
    }

    def __repr__(self):
        return f"<ErrorLog {self.uuid}>"

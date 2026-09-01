#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Methods to store data to Postgresql database."""

import copy
import importlib.resources
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Tuple

import psycopg2.errors
import sqlalchemy.engine.base
from sqlalchemy import MetaData, Table, create_engine, event, exc, exists, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import IntegrityError, OperationalError, StatementError
from sqlalchemy.sql import and_

from gn2pg import _, __version__
from gn2pg.database import build_metadata
from gn2pg.database.migrations import (
    DatabaseStatus,
    database_status,
    stamp_existing_database,
    upgrade_database,
)
from gn2pg.utils import XferStatus

# from gn2pg.logger import logger
logger = logging.getLogger(__name__)


def format_pg_error(error: StatementError) -> str:
    """Limite SQL error output to main informations, without CONTEXT content"""
    diag = getattr(error.orig, "diag", None)
    if diag is None:
        return str(error.orig)

    return "\n".join(
        filter(
            None,
            (
                diag.message_primary,
                f"DETAIL:  {diag.message_detail}" if diag.message_detail else None,
            ),
        )
    )


class _PostgresqlNoticeLogger(list):
    """Log PostgreSQL messages as soon as psycopg2 receives them."""

    def append(self, notice: str) -> None:
        message = notice.rstrip()
        if message.startswith(("DEBUG:", "NOTICE:")):
            logger.debug("SQL: %s", message)
        else:
            logger.info("SQL: %s", message)
        super().append(notice)
        del self[:-50]


def _create_postgresql_engine(url: URL) -> sqlalchemy.engine.base.Engine:
    """Create an engine logging all PostgreSQL NOTICE and INFO messages."""
    engine = create_engine(url, echo=False)

    @event.listens_for(engine, "connect")
    def configure_connection(dbapi_connection, _connection_record) -> None:
        dbapi_connection.notices = _PostgresqlNoticeLogger()
        client_min_messages = "DEBUG1" if logger.isEnabledFor(logging.DEBUG) else "NOTICE"
        with dbapi_connection.cursor() as cursor:
            cursor.execute(f"SET client_min_messages TO {client_min_messages}")
        dbapi_connection.commit()

    return engine


def db_url(config):
    """db connection settings"""
    return {
        "drivername": "postgresql+psycopg2",
        "username": config.database.user,
        "password": config.database.password,
        "host": config.database.host,
        "port": config.database.port,
        "database": config.database.name,
    }


class StorePostgresqlException(Exception):
    """An exception occurred while handling download or store."""


class DataItem:
    """Properties of an observation, for writing to DB."""

    def __init__(self, source: str, metadata: MetaData, conn: Any, elem: dict) -> None:
        """Item elements

        Args:
            source (str): GeoNature source name, for column storage
            metadata (str): SqlAlchemy metadata for data table.
            conn (str): SqlAlchemy connection to database
            elem (dict): Single observation to process and store.

        Returns:
            None
        """
        self._source = source
        self._metadata = metadata
        self._conn = conn
        self._elem = elem

    @property
    def source(self) -> str:
        """Return source name

        Returns:
            str: Source name
        """
        return self._source

    @property
    def metadata(self) -> MetaData:
        """Return SqlAlchemy metadata

        Returns:
            str: SqlAlchemy metadata
        """
        return self._metadata

    @property
    def conn(self) -> Any:
        """Return db connection

        Returns:
            str: db connection
        """
        return self._conn

    @property
    def elem(self) -> dict:
        """Return Single observation to process and store

        Returns:
            str: Observation
        """
        return self._elem


class PostgresqlUtils:
    """Provides create and delete Postgresql database method."""

    def __init__(self, config) -> None:
        self._config = config
        self._db_url = db_url(self._config)
        if self._config.database.querystring:
            self._db_url["query"] = self._config.database.querystring

        self._db = _create_postgresql_engine(URL.create(**self._db_url))
        self._db_schema = self._config.database.schema_import
        self._metadata = build_metadata(self._db_schema)

    def create_json_tables(self) -> None:
        """Upgrade the internal and JSONB tables with Alembic."""
        logger.info(
            _("Connecting to %s database, to finalize creation"),
            self._config.database.name,
        )
        try:
            upgrade_database(
                URL.create(**self._db_url),
                self._config.database.schema_import,
            )
            logger.info("Database successfully upgraded")
        except OperationalError as e:
            logger.critical(_("An error occured while trying to connect to database : %s"), e)

    def migration_status(self) -> DatabaseStatus:
        """Return the current Alembic status for the configured schema."""
        return database_status(URL.create(**self._db_url), self._db_schema)

    def stamp_existing(self) -> None:
        """Validate and stamp an existing pre-Alembic database."""
        stamp_existing_database(URL.create(**self._db_url), self._db_schema)

    def count_json_data(self):
        """Count observations stored in json table, by source and type.

        Returns:
            dict: Count of observations by site and taxonomy.
        """

        result = None
        # Store to database, if enabled
        logger.info(_("Counting datas in database for all sources"))
        # Connect and set path to include VN import schema
        logger.info(_("Connecting to database %s"), self._config.database.name)
        with self._db.connect() as conn:
            query = f"""
                SELECT source, COUNT(uuid)
                    FROM {self._config.database.schema_import}.data_json
                    GROUP BY source;
                """  # noqa: E702

            result = conn.execute(text(query)).fetchall()

        return result

    def custom_script(self, script: str = "to_gnsynthese") -> None:
        """EXecute custom script on DB.
        eg.:  triggers to populate local tables like GeoNature synthese

        Args:
            script (str, optional): custom script path. Defaults to "to_gnsynthese".
        """
        logger.info(_("Start to execute %s script"), script)
        if script == "to_gnsynthese":
            file = importlib.resources.files(  # pylint: disable=too-many-function-args
                __package__ or "gn2pg"
            ).joinpath(  # pylint: disable=too-many-function-args
                "data", "to_gnsynthese.sql"
            )
            logger.info(
                _("You choosed to use internal to_gnsynthese.sql script in schema %s"),
                self._db_schema,
            )
        else:
            if Path(script).is_file():
                logger.info(_("file %s exists, continue"), script)
                file = Path(script)
            else:
                logger.critical(_("file %s DO NOT EXISTS, exit"), script)
                sys.exit(0)
        with open(file, encoding="utf-8") as file_content:
            sql_script = file_content.read()
            sql_script = sql_script.replace("gn2pg_import", self._db_schema)
        try:
            # logger.debug(sqlscript)
            with self._db.begin() as conn:
                conn.execute(text(sql_script))
            logger.info(_("script %s successfully applied"), script)
        except exc.SQLAlchemyError as error:
            logger.critical(str(error))
            logger.critical("failed to apply script %s", script)


class StorePostgresql:
    """Provides store to Postgresql database method."""

    def __init__(self, config):
        self._config = config
        self._db_url = db_url(self._config)
        if self._config.database.querystring:
            self._db_url["query"] = self._config.database.querystring
        self._db = _create_postgresql_engine(URL.create(**self._db_url))
        self._db_schema = self._config.database.schema_import
        self._metadata = build_metadata(self._db_schema)

        self.total_errors: int = 0
        self.count_data_upserts: int = 0
        self.count_data_delete: int = 0
        self.count_data_errors: int = 0
        self.count_metadata_inserts: int = 0
        self.count_metadata_errors: int = 0
        self.import_id: int = None

        # Map Import tables in a single dict for easy reference
        self._table_defs = {
            "data": {
                "type": "data",
                "metadata": self._metadata.tables[self._db_schema + ".data_json"],
            },
            "meta": {
                "type": "metadata",
                "metadata": self._metadata.tables[self._db_schema + ".metadata_json"],
            },
        }

        # self._table_defs["data"]["metadata"] = self._metadata.tables[
        #     self._db_schema + ".data_json"
        # ]

    def __enter__(self):
        logger.debug(_("Entry into StorePostgresql"))
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Finalize connections."""
        logger.debug("Disposing database engine at exit from StorePostgresql")
        self._db.dispose()

    @property
    def version(self):
        """Return version."""
        return __version__

    # ----------------
    # Internal methods
    # ----------------

    def store_1_metadata(
        self,
        controler: str,
        level: str,
        elem: dict,
        uuid_key_name: str = "uuid",
    ):
        """Store 1 metadata item in db (using upsert statement)"""

        try:
            with self._db.begin() as conn:
                rowcount = self._store_1_metadata(
                    conn, controler, level, elem, uuid_key_name=uuid_key_name
                )
            self.count_metadata_inserts += rowcount
        except (IntegrityError, StatementError) as error:
            self.error_log(controler, elem, str(error), uuid=elem.get(uuid_key_name, None))
            if isinstance(error.orig, psycopg2.errors.UniqueViolation):
                logger.warning(
                    _(
                        "A metadata with UUID %(uuid)s from a different source already"
                        " exists in Database: %(error)s",
                    ),
                    {"uuid": elem[uuid_key_name], "error": format_pg_error(error)},
                )
            else:
                logger.critical(
                    _(
                        "One error occurred for data from source %(source)s "
                        "with  %(key)s = %(uuid)s. Error message is %(error)s"
                    ),
                    {
                        "source": self._config.std_name,
                        "key": "uuid",
                        "uuid": elem[uuid_key_name],
                        "error": format_pg_error(error),
                    },
                )
            self.count_metadata_errors += 1

    def _store_1_metadata(
        self,
        conn: sqlalchemy.engine.base.Connection,
        controler: str,
        level: str,
        elem: dict,
        uuid_key_name: str = "uuid",
    ) -> int:
        """Store one metadata item using the caller's transaction."""

        metadata = self._table_defs["meta"]["metadata"]
        # logger.debug(elem[id_key_name])
        exists_stmt = select(
            exists().where(
                metadata.c.source == self._config.std_name,
                metadata.c.controler == controler,
                metadata.c.uuid == elem[uuid_key_name],
                metadata.c.import_id == self.import_id,
            )
        )
        if conn.execute(exists_stmt).scalar():
            return 0

        insert_stmt = insert(metadata).values(
            controler=controler,
            type=self._config.data_type,
            level=level,
            uuid=elem[uuid_key_name],
            source=self._config.std_name,
            item=elem,
            update_ts=datetime.now(),
            import_id=self.import_id,
        )
        do_update_stmt = insert_stmt.on_conflict_do_update(
            constraint=metadata.primary_key,
            set_={"item": elem, "update_ts": datetime.now(), "import_id": self.import_id},
        )
        return conn.execute(do_update_stmt).rowcount

    def store_1_data(
        self,
        controler: str,
        elem: dict,
        id_key_name: str = "id_synthese",
        uuid_key_name: str = "id_perm_sinp",
    ) -> None:
        """Store 1 item in db (using upsert statement)

        Args:
            controler (str): Destionation table
            elem (dict): json data as dict
            id_key_name (str, optional): Data id in source database. Defaults to "id_synthese".
            uuid_key_name (str, optional): data UUID. Defaults to "id_perm_sinp".
        """
        metadata = self._table_defs[controler]["metadata"]
        logger.debug(
            "elem[id_key_name] is %(item)s, id_key_name is %(key)s",
            {"item": elem[id_key_name], "key": id_key_name},
        )
        try:
            metadata_inserts = 0
            with self._db.begin() as conn:
                logger.debug("store_1_data type %s", self._config.data_type)
                for key, value in (
                    ("ca_data", "acquisition framework"),
                    ("jdd_data", "dataset"),
                ):
                    if key in elem and isinstance(elem.get(key), dict):
                        meta_data = elem.pop(key)
                        elem[f"{key.rsplit('_', maxsplit=1)[0]}_uuid"] = meta_data["uuid"]
                        if key == "jdd_data":
                            meta_data["ca_uuid"] = elem["ca_uuid"]
                        metadata_inserts += self._store_1_metadata(
                            conn, controler="metadata", level=value, elem=meta_data
                        )

                insert_stmt = insert(metadata).values(
                    id_data=elem[id_key_name],
                    controler=controler,
                    type=self._config.data_type,
                    uuid=elem[uuid_key_name],
                    source=self._config.std_name,
                    item=elem,
                    update_ts=datetime.now(),
                    import_id=self.import_id,
                )
                do_update_stmt = insert_stmt.on_conflict_do_update(
                    constraint=metadata.primary_key,
                    set_={"item": elem, "update_ts": datetime.now(), "import_id": self.import_id},
                )
                data_upserts = conn.execute(do_update_stmt).rowcount
            self.count_metadata_inserts += metadata_inserts
            self.count_data_upserts += data_upserts
        except (IntegrityError, StatementError) as error:
            # The transaction has already been rolled back before logging the error.
            if isinstance(error.orig, psycopg2.errors.UniqueViolation):
                self.error_log(controler, elem, str(error), uuid=elem.get(uuid_key_name, None))
                logger.warning(
                    _(
                        "A data with UUID %(uuid)s from a different source already"
                        " exists in Database: %(error)s",
                    ),
                    {"uuid": elem[uuid_key_name], "error": format_pg_error(error)},
                )
            else:
                self.error_log(controler, elem, str(error), uuid=elem.get(uuid_key_name, None))
                logger.critical(
                    _(
                        "One error occurred for data from source %(source)s "
                        "with %(key)s = %(uuid)s. Error message is %(error)s"
                    ),
                    {
                        "source": self._config.std_name,
                        "key": "uuid",
                        "uuid": elem[uuid_key_name],
                        "error": format_pg_error(error),
                    },
                )
            self.count_data_errors += 1

    def store_data(
        self,
        controler: str,
        items: list[dict],
        # import_log_id: int,
        id_key_name: str = "id_synthese",
        uuid_key_name: str = "id_perm_sinp",
    ) -> Tuple[int, int, int]:
        """Write items_dict to database.

        Args:
            controler (str): Name of API controler.
            items (list): Data returned from API call.
            id_key_name (str, optional): id key name from source. Defaults to "id_synthese".
            uuid_key_name (str, optional): uuid key name from source. Defaults to "id_perm_sinp".

        Returns:
            int: items dict length
        """
        # Loop on data array to store each element to database
        # self.import_id = import_log_id
        for elem in items:
            try:
                # Convert to json
                self.store_1_data(controler, elem, id_key_name, uuid_key_name)
            except StatementError as error:
                self.error_log(
                    controler,
                    elem,
                    str(error),
                    uuid=elem.get(uuid_key_name, None),
                )
                logger.critical(
                    _(
                        "One error occurred for data from source %(std_name)s "
                        "with %(id_key_name)s = %(id)s"
                    ),
                    {
                        "std_name": self._config.std_name,
                        "id_key_name": id_key_name,
                        "id": elem[id_key_name],
                    },
                )
        logger.info(
            _(
                "%(count_data_upserts)s data and %(count_metadata_inserts)s metadata "
                "have been stored in db from source %(std_name)s (%(count_data_errors)s "
                "error occurred)"
            ),
            {
                "count_data_upserts": self.count_data_upserts,
                "count_metadata_inserts": self.count_metadata_inserts,
                "std_name": self._config.std_name,
                "count_data_errors": self.count_data_errors + self.count_metadata_errors,
            },
        )
        return (
            len(items),
            self.count_data_upserts,
            self.count_data_errors,
            self.count_metadata_inserts,
            self.count_metadata_errors,
        )

    def store_metadata(self, items: list[dict]) -> Tuple[int, int, int]:
        """Store acquisition frameworks and their datasets from a metadata export.

        A metadata export item contains the acquisition framework in ``jsonb_insert``
        and its datasets in the nested ``datasets`` array.
        """
        initial_upserts = self.count_metadata_inserts
        initial_errors = self.count_metadata_errors

        for exported_item in items:
            metadata_item = exported_item
            if not isinstance(metadata_item, dict) or not metadata_item.get("uuid"):
                logger.error(
                    _("Invalid metadata export item from source %(source)s: %(item)s"),
                    {"source": self._config.std_name, "item": exported_item},
                )
                self.count_metadata_errors += 1
                continue

            acquisition_framework = copy.deepcopy(metadata_item)
            datasets = acquisition_framework.pop("datasets", []) or []
            acquisition_framework_uuid = acquisition_framework["uuid"]

            # The acquisition framework must exist before dataset triggers run.
            self.store_1_metadata(
                controler="metadata",
                level="acquisition framework",
                elem=acquisition_framework,
            )

            for exported_dataset in datasets:
                if not isinstance(exported_dataset, dict) or not exported_dataset.get("uuid"):
                    logger.error(
                        _("Invalid dataset in metadata export from source %(source)s: %(item)s"),
                        {"source": self._config.std_name, "item": exported_dataset},
                    )
                    self.count_metadata_errors += 1
                    continue
                dataset = copy.deepcopy(exported_dataset)
                dataset["ca_uuid"] = acquisition_framework_uuid
                self.store_1_metadata(
                    controler="metadata",
                    level="dataset",
                    elem=dataset,
                )

        return (
            len(items),
            self.count_metadata_inserts - initial_upserts,
            self.count_metadata_errors - initial_errors,
        )

    # ----------------
    # External methods
    # ----------------

    def delete_data(
        self,
        items: list,
        id_key_name: str = "id_synthese",
        controler: str = "data",
    ) -> int:
        """Delete observations stored in database.

        Args:
            items (list): items to delete
            id_key_name (str, optional): id key name from source. Defaults to "id_synthese".
            controler (str, optional): Name of API controler. Defaults to "data".

        Returns:
            int: Count of items deleted.
        """
        del_count = 0
        # Store to database, if enabled
        logger.debug(
            _(
                "Api returned %(length)s row to delete from source %(source)s "
                "(controler %(controler)s)"
            ),
            {"length": str(len(items)), "source": self._config.name, "controler": controler},
        )
        keys = [item[id_key_name] for item in items]
        with self._db.begin() as conn:
            deleted_data = conn.execute(
                self._table_defs["data"]["metadata"]
                .delete()
                .where(
                    and_(
                        self._table_defs["data"]["metadata"].c.id_data.in_(keys),
                        self._table_defs["data"]["metadata"].c.controler == controler,
                        self._table_defs["data"]["metadata"].c.source == self._config.std_name,
                    )
                )
            )
            del_count += deleted_data.rowcount
        logger.debug(
            _(
                "%(count)s rows have been deleted from source %(source)s "
                "(controler %(controler)s)"
            ),
            {"count": str(del_count), "source": self._config.name, "controler": controler},
        )

        return del_count

    def import_log(self, controler: str, values: Optional[dict] = None):
        """Write download log entries to database.

        Args:
            controler (str): Name of API controler.
            values (dict, optional): Field values. Defaults to None
        """
        # Store to database, if enabled
        metadata: Table = self._metadata.tables[
            self._config.database.schema_import + "." + "import_log"
        ]
        if values is None:
            values = {}
        if not self.import_id:
            stmt = (
                metadata.insert()
                .values(source=self._config.std_name, controler=controler, **values)
                .returning(metadata.c.id)
            )
        else:
            stmt = (
                metadata.update()
                .where(metadata.c.id == self.import_id)
                .values(**values)
                .returning(metadata.c.id)
            )
        with self._db.begin() as conn:
            result = conn.execute(stmt)
            self.import_id = result.scalar()
        return self.import_id

    def import_get(self, controler: str) -> Optional[str]:
        """Get last download timestamp from database.

        Args:
            controler (str): Controler name

        Returns:
            Optional[str]: Return last increment timestamp if exists
        """
        row = None
        metadata = self._metadata.tables[self._config.database.schema_import + "." + "import_log"]
        stmt = (
            select(metadata.c.xfer_start_ts)
            .where(
                and_(
                    metadata.c.source == self._config.std_name,
                    metadata.c.controler == controler,
                    metadata.c.xfer_status == XferStatus.success,
                )
            )
            .order_by(metadata.c.xfer_start_ts.desc())
        )
        with self._db.connect() as conn:
            result = conn.execute(stmt)
            row = result.fetchone()

        return row[0] if row is not None else None

    def error_log(  # pylint: disable=R0917
        self,
        controler: str,
        item: dict,
        error: str,
        uuid: str = None,
        last_ts: datetime = datetime.now(),
    ) -> None:
        """Store errors in database

        Args:
            controler (str): Controler name
            item (dict): Item
            error (str): SQLAlchemy Error
            uuid (str, optional): Data or metadata UUID. Defaults to None.
            last_ts (datetime, optional): [description]. Defaults to datetime.now().
        """

        with self._db.begin() as conn:
            self._error_log(conn, controler, item, error, uuid=uuid, last_ts=last_ts)

    def _error_log(  # pylint: disable=R0917
        self,
        conn: sqlalchemy.engine.base.Connection,
        controler: str,
        item: dict,
        error: str,
        uuid: str = None,
        last_ts: datetime = datetime.now(),
    ) -> None:
        """Store an error using the caller's transaction."""
        metadata = self._metadata.tables[self._config.database.schema_import + "." + "error_log"]
        exists_stmt = select(
            exists().where(
                metadata.c.source == self._config.std_name,
                metadata.c.controler == controler,
                metadata.c.uuid == uuid,
                metadata.c.import_id == self.import_id,
            )
        )
        if not conn.execute(exists_stmt).scalar():
            insert_stmt = insert(metadata).values(
                source=self._config.std_name,
                controler=controler,
                uuid=uuid,
                item=item,
                last_ts=last_ts,
                error=error,
                import_id=self.import_id,
            )
            conn.execute(insert_stmt)

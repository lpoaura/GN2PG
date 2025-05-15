#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Methods to store data to Postgresql database."""
import importlib.resources
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Tuple

import psycopg2.errors
import sqlalchemy.engine.base
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    PrimaryKeyConstraint,
    String,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
    exc,
    exists,
    func,
    select,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID, insert
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import IntegrityError, OperationalError, StatementError
from sqlalchemy.sql import and_

from gn2pg import _, __version__
from gn2pg.utils import XferStatus

# from gn2pg.logger import logger
logger = logging.getLogger(__name__)


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

        self._db = create_engine(URL.create(**self._db_url), echo=False)
        self._db_schema = self._config.database.schema_import
        self._metadata = MetaData(schema=self._db_schema)
        try:
            self._metadata.reflect(self._db)
        except OperationalError as e:
            logger.critical(_("An error occured while trying to connect to database : %s"), e)
            sys.exit(0)

    # ----------------
    # Internal methods
    # ----------------

    def _create_table(self, name, *cols) -> None:
        """Check if table exists, and create it if not

        Parameters
        ----------
        name : str
            Table name.
        cols : list
            Data returned from API call.

        """
        # Store to database, if enabled
        if f"{self._config.database.schema_import}.{name}" not in self._metadata.tables:
            logger.info("Table %s not found => Creating it", name)
            table = Table(name, self._metadata, *cols)
            table.create(self._db)
        else:
            logger.info("Table %s already exists => Keeping it", name)

    def _create_import_log(self) -> None:
        """Create import_log table if it does not exist."""
        self._create_table(
            "import_log",
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("source", String, nullable=False, index=True),
            Column("controler", String, nullable=False),
            Column("xfer_type", String, index=True, nullable=True),
            Column("xfer_status", String, nullable=True),
            Column(
                "xfer_start_ts",
                DateTime,
                nullable=False,
            ),
            Column(
                "xfer_end_ts",
                DateTime,
                nullable=True,
            ),
            Column("api_count_items", Integer, nullable=False, server_default="0"),
            Column("api_count_errors", Integer, nullable=False, server_default="0"),
            Column("data_count_upserts", Integer, nullable=False, server_default="0"),
            Column("data_count_delete", Integer, nullable=False, server_default="0"),
            Column("data_count_errors", Integer, nullable=False, server_default="0"),
            Column("metadata_count_upserts", Integer, nullable=False, server_default="0"),
            Column("metadata_count_errors", Integer, nullable=False, server_default="0"),
            Column("xfer_http_status", Integer, index=True, nullable=True),
            Column("xfer_filters", JSONB, server_default="{}"),
            Column("comment", Text, nullable=True, default=None),
        )

    def _create_error_log(self) -> None:
        """Create error_log table if table does not exist."""
        self._create_table(
            "error_log",
            Column("source", String, nullable=False),
            Column("uuid", UUID, nullable=False, index=True),
            Column("controler", String, nullable=False),
            Column("last_ts", DateTime, server_default=func.now(), nullable=False),
            Column("item", JSONB),
            Column("error", String),
            Column(
                "import_id",
                Integer,
                ForeignKey("import_log.id", ondelete="CASCADE", onupdate="CASCADE"),
                index=True,
            ),
        )

    def _create_data_json(self) -> None:
        """Create observations_json table if it does not exist."""
        self._create_table(
            "data_json",
            Column("source", String, nullable=False),
            Column("controler", String, nullable=False),
            Column("type", String, nullable=False),
            Column("id_data", Integer, nullable=False, index=True),
            Column("uuid", UUID, index=True),
            Column("item", JSONB, nullable=False),
            Column(
                "update_ts",
                DateTime,
                server_default=func.now(),
                nullable=False,
            ),
            Column(
                "import_id",
                Integer,
                ForeignKey("import_log.id", onupdate="CASCADE"),
            ),
            PrimaryKeyConstraint("id_data", "source", "type", name="pk_source_data"),
            UniqueConstraint("uuid", name="unique_uuid"),
        )

    def _create_metadata_json(self) -> None:
        """Create observations_json table if it does not exist."""
        self._create_table(
            "metadata_json",
            Column("source", String, nullable=False),
            Column("controler", String, nullable=False),
            Column("type", String, nullable=False),
            Column("level", String, nullable=False),
            Column("uuid", UUID, index=True),
            Column("item", JSONB, nullable=False),
            Column(
                "update_ts",
                DateTime,
                server_default=func.now(),
                nullable=False,
            ),
            Column(
                "import_id",
                Integer,
                ForeignKey("import_log.id", onupdate="CASCADE"),
            ),
            PrimaryKeyConstraint("uuid", "source", name="pk_source_metadata"),
            UniqueConstraint("uuid", name="metadata_unique_uuid"),
        )

    def create_json_tables(self) -> None:
        """Create all internal and jsonb tables."""
        logger.info(
            _("Connecting to %s database, to finalize creation"),
            self._config.database.name,
        )
        try:
            with self._db.connect() as conn:
                # Create extensions
                try:
                    ext_queries = (
                        'CREATE EXTENSION IF NOT EXISTS "pgcrypto";',
                        'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";',
                    )
                    for query in ext_queries:
                        logger.debug(_("Execute: %s"), query)
                        conn.execute(text(query))
                    logger.info("PostgreSQL extensions successfully created")
                except exc.SQLAlchemyError as error:
                    logger.critical(str(error))
                # Create import schema
                try:
                    query = f"""
                    CREATE SCHEMA IF NOT EXISTS {self._config.database.schema_import}
                    AUTHORIZATION {self._config.database.user};
                    """  # noqa: E702
                    logger.debug(_("Execute: %s"), query)
                    conn.execute(text(query))
                    logger.info(
                        (
                            _("Schema %s owned by %s successfully created"),
                            self._config.database.schema_import,
                            self._config.database.user,
                        )
                    )
                except exc.SQLAlchemyError as error:
                    logger.critical(
                        _("Failed to create %s schema"),
                        self._config.database.schema_import,
                    )
                    logger.critical(str(error))
                # Set path to include VN import schema

                # Check if tables exist or else create them
                self._create_import_log()
                self._create_error_log()
                self._create_data_json()
                self._create_metadata_json()

                conn.close()

                self._db.dispose()
        except OperationalError as e:
            logger.critical(_("An error occured while trying to connect to database : %s"), e)

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
            conn.close()

        return result

    def custom_script(self, script: str = "to_gnsynthese") -> None:
        """EXecute custom script on DB.
        eg.:  triggers to populate local tables like GeoNature synthese

        Args:
            script (str, optional): custom script path. Defaults to "to_gnsynthese".
        """
        logger.info(_("Start to execute %s script"), script)
        conn = self._db.connect()
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
            with self._db.connect() as conn:
                conn.execute(text(sql_script))
                conn.close()
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
        self._db: sqlalchemy.engine.base.Engine = create_engine(
            URL.create(**self._db_url), echo=False
        )
        self._db_schema = self._config.database.schema_import
        self._metadata = MetaData(schema=self._db_schema)
        try:
            self._metadata.reflect(self._db)
        except OperationalError as e:
            logger.critical(_("An error occured while trying to connect to database : %s"), e)
            sys.exit(0)

        self._conn = self._db.connect()

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
        logger.debug("Closing database connection at exit from StorePostgresql")
        self._conn.close()

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

        metadata = self._table_defs["meta"]["metadata"]
        # logger.debug(elem[id_key_name])
        exists_stmt = select(
            [
                exists().where(
                    metadata.c.source == self._config.std_name,
                    metadata.c.controler == controler,
                    metadata.c.uuid == elem[uuid_key_name],
                    metadata.c.import_id == self.import_id,
                )
            ]
        )
        if not self._conn.execute(exists_stmt).scalar():
            try:
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
                result = self._conn.execute(do_update_stmt)
                self.count_metadata_inserts += result.rowcount
                self._conn.execute("COMMIT")
            except (IntegrityError, exc.StatementError) as error:
                # Check if the original exception is a UniqueViolation
                self._conn.execute("ROLLBACK")
                if isinstance(error.orig, psycopg2.errors.UniqueViolation):
                    self.error_log(controler, elem, str(error), uuid=elem.get(uuid_key_name, None))
                    # if logger.getEffectiveLevel() >
                    logger.warning(
                        _(
                            "A metadata with UUID %s from a different source already"
                            " exists in Database: %s",
                        ),
                        elem["uuid"],
                        str(error),
                    )
                else:
                    self.error_log(controler, elem, str(error), uuid=elem.get(uuid_key_name, None))
                    logger.critical(
                        _(
                            "One error occurred for data from source %s "
                            "with %s = %s. Error message is %s"
                        ),
                        self._config.std_name,
                        "uuid",
                        elem["uuid"],
                        str(error),
                    )
                self.count_metadata_errors += 1

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
        logger.debug("elem[id_key_name] is %s, id_key_name is %s", elem[id_key_name], id_key_name)
        metadata_infos = {"ca_data": "acquisition framework", "jdd_data": "dataset"}
        try:
            logger.debug("store_1_data type %s", self._config.data_type)
            for key, value in metadata_infos.items():
                if key in elem and isinstance(elem.get(key), dict):
                    meta_data = elem.pop(key)
                    elem[f"{key.rsplit('_', maxsplit=1)[0]}_uuid"] = meta_data[
                        "uuid"
                    ]  # Generate key "{ca,jdd}_uuid"
                    if key == "jdd_data":
                        meta_data["ca_uuid"] = (
                            elem["ca_data"]["uuid"] if "ca_data" in elem else elem["ca_uuid"]
                        )
                    self.store_1_metadata(controler="metadata", level=value, elem=meta_data)

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
            result = self._conn.execute(do_update_stmt)
            self.count_data_upserts += result.rowcount
            self._conn.execute("COMMIT")
        except (IntegrityError, exc.StatementError) as error:
            # Check if the original exception is a UniqueViolation
            self._conn.execute("ROLLBACK")
            if isinstance(error.orig, psycopg2.errors.UniqueViolation):
                self.error_log(controler, elem, str(error), uuid=elem.get(uuid_key_name, None))
                logger.warning(
                    _(
                        "A data with UUID %s from a different source already"
                        " exists in Database: %s",
                    ),
                    elem[uuid_key_name],
                    str(error),
                )
            else:
                self.error_log(controler, elem, str(error), uuid=elem.get(uuid_key_name, None))
                logger.critical(
                    _(
                        "One error occurred for data from source %s "
                        "with %s = %s. Error message is %s"
                    ),
                    self._config.std_name,
                    id_key_name,
                    elem[id_key_name],
                    str(error),
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
                    _("One error occurred for data from source %s with %s = %s"),
                    self._config.std_name,
                    id_key_name,
                    elem[id_key_name],
                )
        logger.info(
            _("%s data and %s metadata have been stored in db from source %s (%s error occurred)"),
            self.count_data_upserts,
            self.count_metadata_inserts,
            self._config.std_name,
            self.count_data_errors + self.count_metadata_errors,
        )
        return (
            len(items),
            self.count_data_upserts,
            self.count_data_errors,
            self.count_metadata_inserts,
            self.count_metadata_errors,
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
            _("Api returned %s row to delete from source %s (controler %s)"),
            str(len(items)),
            self._config.name,
            controler,
        )
        keys = [item[id_key_name] for item in items]
        deleted_data = self._conn.execute(
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
            _("%s rows have been deleted from source %s (controler %s)"),
            str(del_count),
            self._config.name,
            controler,
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
        result = self._conn.execute(stmt)
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
            select([metadata.c.xfer_start_ts])
            .where(
                and_(
                    metadata.c.source == self._config.std_name,
                    metadata.c.controler == controler,
                    metadata.c.xfer_status == XferStatus.success,
                )
            )
            .order_by(metadata.c.xfer_start_ts.desc())
        )
        result = self._conn.execute(stmt)
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

        metadata = self._metadata.tables[self._config.database.schema_import + "." + "error_log"]
        exists_stmt = select(
            [
                exists().where(
                    metadata.c.source == self._config.std_name,
                    metadata.c.controler == controler,
                    metadata.c.uuid == uuid,
                    metadata.c.import_id == self.import_id,
                )
            ]
        )
        print(exists_stmt)
        if not self._conn.execute(exists_stmt).scalar():
            insert_stmt = insert(metadata).values(
                source=self._config.std_name,
                controler=controler,
                uuid=uuid,
                item=item,
                last_ts=last_ts,
                error=error,
                import_id=self.import_id,
            )
            self._conn.execute(insert_stmt)

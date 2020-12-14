#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Methods to store Biolovision data to Postgresql database.


Methods

- store_data      - Store generic data structure to file

Properties

-

"""
import logging

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    PrimaryKeyConstraint,
    String,
    Table,
    create_engine,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID, insert
from sqlalchemy.engine.url import URL
from sqlalchemy.sql import and_

from . import _, __version__

# logger = logging.getLogger("transfer_gn.store_postgresql")
logger = logging.getLogger("transfer_gn.store_postgresql")


class StorePostgresqlException(Exception):
    """An exception occurred while handling download or store. """


class DataItem:
    """Properties of an observation, for writing to DB."""

    def __init__(self, source: str, metadata: str, conn: str, elem: dict) -> None:
        """Item elements

        Args:
            source (str): GeoNature source name, for column storage
            metadata (str): SqlAlchemy metadata for synthese data table.
            conn (str): SqlAlchemy connection to database
            elem (dict): Single observation to process and store.

        Returns:
            None
        """
        self._source = source
        self._metadata = metadata
        self._conn = conn
        self._elem = elem
        return None

    @property
    def source(self) -> str:
        """Return source name

        Returns:
            str: Source name
        """
        return self._source

    @property
    def metadata(self) -> str:
        """Return SqlAlchemy metadata

        Returns:
            str: SqlAlchemy metadata
        """
        return self._metadata

    @property
    def conn(self) -> str:
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


def store_1_observation(item: dict) -> None:
    """Process and store a single observation.

    - find insert or update date
    - store json in Postgresql

    Args:
        item (dict): ObservationItem, Observation item containing all parameters.

    Returns:
        None
    """
    # Insert simple observations,
    # each row contains uniq_id, update timestamp and full json body
    elem = item.elem
    uniq_id = elem["ID_perm_SINP"]
    logger.debug(
        f"Storing observation {uniq_id} to database",
    )
    # Find last update timestamp
    if "Date_modification" in elem:
        update_date = elem["Date_modification"]
    else:
        update_date = elem["Date_creation"]

    # Store in Postgresql
    metadata = item.metadata
    source = item.source
    insert_stmt = insert(metadata).values(
        uuid=uniq_id,
        source=source,
        update_ts=update_date,
        item=elem,
    )
    do_update_stmt = insert_stmt.on_conflict_do_update(
        constraint=metadata.primary_key,
        set_=dict(update_ts=update_date, item=elem),
        where=(metadata.c.update_ts < update_date),
    )

    item.conn.execute(do_update_stmt)
    return None


class PostgresqlUtils:
    """Provides create and delete Postgresql database method."""

    def __init__(self, config):
        self._config = config
        self._db_url = {
            "drivername": "postgresql+psycopg2",
            "username": self._config.db_user,
            "password": self._config.db_password,
            "host": self._config.db_host,
            "port": self._config.db_port,
            "database": self._config.db_name,
        }
        if self._config.db_querystring:
            self._db_url["query"]: self._config.db_querystring

    # ----------------
    # Internal methods
    # ----------------

    def _create_table(self, name, *cols):
        """Check if table exists, and create it if not

        Parameters
        ----------
        name : str
            Table name.
        cols : list
            Data returned from API call.

        """
        # Store to database, if enabled
        if (self._config.db_schema_import + "." + name) not in self._metadata.tables:
            logger.info("Table %s not found => Creating it", name)
            table = Table(name, self._metadata, *cols)
            table.create(self._db)
        else:
            logger.info("Table %s already exists => Keeping it", name)
        return None

    def _create_download_log(self):
        """Create download_log table if it does not exist."""
        self._create_table(
            "download_log",
            Column("uuid", Integer, primary_key=True),
            Column("source", String, nullable=False, index=True),
            Column("controler", String, nullable=False),
            Column("download_ts", DateTime, server_default=func.now(), nullable=False),
            Column("error_count", Integer, index=True),
            Column("http_status", Integer, index=True),
            Column("comment", String),
        )
        return None

    def _create_increment_log(self):
        """Create increment_log table if it does not exist."""
        self._create_table(
            "increment_log",
            Column("source", String, primary_key=True, nullable=False),
            Column("last_ts", DateTime, server_default=func.now(), nullable=False),
        )
        return None

    def _create_datasets_json(self):
        """Create entities_json table if it does not exist."""
        self._create_table(
            "datasets_json",
            Column("uuid", UUID, nullable=False),
            Column("source", String, nullable=False),
            Column("item", JSONB, nullable=False),
            PrimaryKeyConstraint("uuid", "source", name="meta_json_pk"),
        )
        return None

    def _create_synthese_json(self):
        """Create observations_json table if it does not exist."""
        self._create_table(
            "synthese_json",
            Column("uuid", UUID, nullable=False, index=True),
            Column("source", String, nullable=False),
            Column("item", JSONB, nullable=False),
            Column("update_ts", Integer, nullable=False),
            PrimaryKeyConstraint("uuid", "source", name="data_json_pk"),
        )
        return None

    def create_json_tables(self):
        """Create all internal and jsonb tables."""
        # Store to database, if enabled
        # Initialize interface to Postgresql DB
        # db_url = {
        #     "drivername": "postgresql+psycopg2",
        #     "username": self._config.db_user,
        #     "password": self._config.db_pw,
        #     "host": self._config.db_host,
        #     "port": self._config.db_port,
        #     "database": self._config.db_name,
        # }
        # if self._config.db_querystring:
        #     db_url["query"]: self._config.db_querystring
        # Connect to database
        logger.info(
            f"Connecting to {self._config.db_name} database, to finalize creation"
        )
        self._db = create_engine(URL(**self._db_url), echo=False)
        conn = self._db.connect()
        # Create extensions
        try:
            ext_queries = (
                "CREATE EXTENSION IF NOT EXISTS pgcrypto;",
                'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";',
                "CREATE EXTENSION IF NOT EXISTS postgis;",
            )
            for q in ext_queries:
                logger.debug(f"Execute: {q}")
                conn.execute(q)
            logger.info("PostgreSQL extensions successfully created")
        except Exception as e:
            logger.critical(f"PostgreSQL extensions create failed : {e}")
        # Create import schema
        try:
            query = f"CREATE SCHEMA IF NOT EXISTS {self._config.db_schema_import} AUTHORIZATION {self._config.db_user}"
            logger.debug(f"Execute: {query}")
            conn.execute(query)
            logger.info(
                f"Schema {self._config.db_schema_import} owned by {self._config.db_user} successfully created"
            )
        except Exception as e:
            logger.critical(f"Failed to create {self._config.db_schema_import} schema")
            logger.critical("{e}")

        # Set path to include VN import schema
        dbschema = self._config.db_schema_import
        self._metadata = MetaData(schema=dbschema)
        self._metadata.reflect(self._db)

        # Check if tables exist or else create them
        self._create_download_log()
        self._create_increment_log()
        self._create_datasets_json()
        self._create_synthese_json()

        conn.close()
        self._db.dispose()

        return None

    def count_json_data(self):
        """Count observations stored in json table, by site and taxonomy.

        Returns
        -------
        dict
            Count of observations by site and taxonomy.
        """
        result = None
        # Store to database, if enabled
        if self._config.db_enabled:
            logger.info(_("Counting datas in database for all sources"))
            # Connect and set path to include VN import schema
            logger.info(_("Connecting to database %s"), self._config.db_name)
            self._db = create_engine(URL(**self._db_url), echo=False)
            conn = self._db.connect()
            dbschema = self._config.db_schema_import
            self._metadata = MetaData(schema=dbschema)
            # self._metadata.reflect(self._db)

            text = """
            SELECT source, COUNT(uuid)
                FROM {}.data_json
                GROUP BY source;
            """.format(
                dbschema
            )

            result = conn.execute(text).fetchall()

        return result


class StorePostgresql:
    """Provides store to Postgresql database method."""

    def __init__(self, config):
        self._config = config
        self._db_url = {
            "drivername": "postgresql+psycopg2",
            "username": self._config.db_user,
            "password": self._config.db_password,
            "host": self._config.db_host,
            "port": self._config.db_port,
            "database": self._config.db_name,
        }
        if self._config.db_querystring:
            self._db_url["query"]: self._config.db_querystring

        dbschema = self._config.db_schema_import
        self._metadata = MetaData(schema=dbschema)
        logger.info(_("Connecting to database %s"), self._config.db_name)

        # Connect and set path to include VN import schema
        self._db = create_engine(URL(**self._db_url), echo=False)
        self._conn = self._db.connect()

        # Get dbtable definition
        self._metadata.reflect(bind=self._db, schema=dbschema)

        # Map Import tables in a single dict for easy reference
        self._table_defs = {
            "data": {"type": "data", "metadata": None},
            "meta": {"type": "metadata", "metadata": None},
        }

        self._table_defs["data"]["metadata"] = self._metadata.tables[
            dbschema + ".synthese_json"
        ]
        self._table_defs["meta"]["metadata"] = self._metadata.tables[
            dbschema + ".datasets_json"
        ]

        return None

    def __enter__(self):
        logger.debug("Entry into StorePostgresql")
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
    def _store_simple(self, controler, items_dict):
        """Write items_dict to database.

        Converts each element to JSON and store to database in a tables
        named from controler.

        Parameters
        ----------
        controler : str
            Name of API controler.
        items_dict : dict
            Data returned from API call.

        Returns
        -------
        int
            Count of items stored (not exact for observations, due to forms).
        """

        # Loop on data array to store each element to database
        logger.info(
            "Storing %d items from %s of source %s",
            len(items_dict["data"]),
            controler,
            self._config.site,
        )
        metadata = self._table_defs[controler]["metadata"]
        for elem in items_dict["items"]:
            # Convert to json
            logger.debug(_("Storing element %s"), elem)
            insert_stmt = insert(metadata).values(
                uuid=elem["ID_perm_SINP"], source=self._config.source, item=elem
            )
            do_update_stmt = insert_stmt.on_conflict_do_update(
                constraint=metadata.primary_key, set_=dict(item=elem)
            )
            self._conn.execute(do_update_stmt)

        return len(items_dict["items"])

    def _store_observation(self, controler, items_dict):
        """Iterate through observations or forms and store.

        Checks if sightings or forms and iterate on each sighting
        - find insert or update date
        - simplity data to remove redundant items: dates... (TBD)
        - add x, y transform to local coordinates
        - store json in Postgresql

        Parameters
        ----------
        controler : str
            Name of API controler.
        items_dict : dict
            Data returned from API call.

        Returns
        -------
        int
            Count of items stored (not exact for observations, due to forms).
        """
        # Insert simple sightings, each row contains id, update timestamp and
        # full json body
        count_data = 0
        items = items_dict["items"]
        logger.debug(_("Storing %d single data"), len(items))
        for i in range(0, len(items)):
            elem = items[i]
            # Write observation to database
            store_1_observation(
                DataItem(
                    self._config.source,
                    self._table_defs[controler]["metadata"],
                    self._conn,
                    elem,
                )
            )
            count_data += 1

        logger.debug(f"Stored {count_data} data to database")
        return count_data

    # ---------------
    # External methods
    # ---------------

    def delete_data(self, obs_list):
        """Delete observations stored in database.

        Parameters
        ----------
        data_list : list
            Data returned from API call.

        Returns
        -------
        int
            Count of items deleted.
        """
        del_count = 0
        # Store to database, if enabled
        logger.info(f"Deleting {len(obs_list)} datas from database")
        for data in data_list:
            nd = self._conn.execute(
                self._table_defs["data"]["metadata"]
                .delete()
                .where(
                    and_(
                        self._table_defs["observations"]["metadata"].c.uuid == data,
                        self._table_defs["observations"]["metadata"].c.source
                        == self._config.source,
                    )
                )
            )
            del_count += nd.rowcount

        return del_count

    def log(self, site, controler, error_count=0, http_status=0, comment=""):
        """Write download log entries to database.

        Parameters
        ----------
        source : str
            GeoNature source name.
        controler : str
            Name of API controler.
        error_count : integer
            Number of errors during download.
        http_status : integer
            HTTP status of latest download.
        comment : str
            Optional comment, in free text.
        """
        # Store to database, if enabled
        metadata = self._metadata.tables[
            self._config.db_schema_import + "." + "download_log"
        ]
        stmt = metadata.insert().values(
            source=site,
            controler=controler,
            error_count=error_count,
            http_status=http_status,
            comment=comment,
        )
        self._conn.execute(stmt)

        return None

    def increment_log(self, source, last_ts):
        """Write last increment timestamp to database.

        Parameters
        ----------
        source : str
            GeoNature source name.

        last_ts : timestamp
            Timestamp of last update of this taxo_group.
        """
        # Store to database, if enabled
        metadata = self._metadata.tables[
            self._config.db_schema_import + "." + "increment_log"
        ]

        insert_stmt = insert(metadata).values(source=source, last_ts=last_ts)
        do_update_stmt = insert_stmt.on_conflict_do_update(
            constraint=metadata.primary_key, set_=dict(last_ts=last_ts)
        )
        self._conn.execute(do_update_stmt)

        return None

    def increment_get(self, source):
        """Get last increment timestamp from database.

        Parameters
        ----------
        source : str
            GeoNature source name.

        Returns
        -------
        timestamp
            Timestamp of last update of this taxo_group.
        """
        row = None
        # Store to database, if enabled
        metadata = self._metadata.tables[
            self._config.db_schema_import + "." + "increment_log"
        ]
        stmt = select([metadata.c.last_ts]).where(metadata.c.source == source)
        result = self._conn.execute(stmt)
        row = result.fetchone()

        if row is None:
            return None
        else:
            return row[0]

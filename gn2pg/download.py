"""Methods to download from VisioNature and store to file.


Methods

- download_taxo_groups      - Download and store taxo groups

Properties

-

"""

import json
import logging
from datetime import datetime
from functools import partial
from multiprocessing import Queue
from multiprocessing.pool import ThreadPool
from threading import Thread
from typing import Callable, List, Optional

from requests.exceptions import HTTPError, InvalidSchema, RetryError
from urllib3.exceptions import ResponseError

from gn2pg import _, __version__
from gn2pg.api import DataAPI, ExportModuleNotFoundError
from gn2pg.check_conf import Gn2PgSourceConf
from gn2pg.store_postgresql import StorePostgresql
from gn2pg.utils import XferStatus

# from gn2pg.logger import logger

logger = logging.getLogger(__name__)


class DownloadGnException(Exception):
    """An exception occurred while handling download or store."""


class NotImplementedException(DownloadGnException):
    """Feature not implemented."""


class DownloadGn:
    """Top class, not for direct use.
    Provides internal and template methods."""

    def __init__(
        self, config: Gn2PgSourceConf, api_instance: DataAPI, backend: StorePostgresql
    ) -> None:
        self._config = config

        self._api_instance = api_instance
        self._backend = backend
        max_retry = config.max_retry
        max_requests = config.max_requests
        self.queue: Queue = Queue()

        # Import log values
        self.import_log_id = None
        self.api_count_items = 0
        self.api_count_errors = 0
        self.data_count_upserts = 0
        self.data_count_delete = 0
        self.data_count_errors = 0
        self.metadata_count_upserts = 0
        self.metadata_count_errors = 0
        self.xfer_type = ""
        self.xfer_filters = {}
        self.xfer_status = XferStatus.init
        self.xfer_comment = None

        self._limits = {
            "max_retry": max_retry,
            "max_requests": max_requests,
        }

        # Init import log
        self.import_log_id = self._backend.import_log(
            controler=self._api_instance.controler,
            values={"xfer_status": self.xfer_status, "xfer_start_ts": datetime.now()},
        )

    @property
    def version(self) -> str:
        """Return version."""
        return __version__

    @property
    def transfer_errors(self) -> int:
        """Return the number of HTTP errors during this session."""
        return self._api_instance.transfer_errors

    @property
    def name(self) -> str:
        """Return the controler name."""
        return self._api_instance.controler

    # ----------------
    # Internal methods
    # ----------------

    # ---------------
    # Generic methods
    # ---------------
    def launch_threads(self, nb_threads: int, func: Callable, pages: list, store=True) -> None:
        """
        Launch 1 + nb_threads threads to execute a function func on a list of pages

        Args:
            nb_threads (int): number of threads to compute the function on the pages
            func (Callable): function that each thread will call
            pages (list): list of pages
            store (bool): if True, display Storing in logger
        """

        def report(queue) -> None:
            """
            From a Queue, get the progress, increase it and log it
            """
            progress = 0
            try:
                while True:
                    response = queue.get()
                    if response in ("DONE", "EXIT"):
                        break
                    progress += response["len_items"]
                    # self.api_count_items = response["total_len"]
                    perc_progress = round(progress / response["total_len"] * 100, 2)

                    # if store:
                    #     self.data_count_upserts = progress

                    if response.get("total_len", 0) > 0:
                        msg = _("Stores") if store else _("Deletes")
                        logger.info(
                            _(
                                "%(action)s %(item_count)d datas "
                                "(%(progress)d/%(total)d %(percentage).2f %%) from "
                                "%(source)s %(controler)s"
                            ),
                            {
                                "action": msg,
                                "item_count": response["len_items"],
                                "progress": progress,
                                "total": response["total_len"],
                                "percentage": perc_progress,
                                "source": self._config.name,
                                "controler": self._api_instance.controler,
                            },
                        )
            except Exception as e:  # pylint: disable=W0718
                errors.append(e)
                self.api_count_errors += 1

        # The Queue enables the report thread to get the progress from other threads
        self.queue: Queue = Queue()
        errors: List[Exception] = []

        # Initialize and start the report thread
        report_thread = Thread(target=report, args=[self.queue])
        report_thread.start()

        # Start the worker threads
        try:
            with ThreadPool(nb_threads) as worker_pool:
                worker_pool.map(partial(func, queue=self.queue), pages)
        finally:
            self.queue.put("DONE")
            report_thread.join()
        return errors

    def download(self, page: str, queue: Queue) -> None:
        """
        Download a page and store the progress in the provided queue

        Args:
            page (str): url to download
            queue (Queue): gather the progress
        """
        response = self.process_progress(page=page)

        (
            _threated_items,
            self.data_count_upserts,
            self.data_count_errors,
            self.metadata_count_upserts,
            self.metadata_count_errors,
        ) = self._backend.store_data(self._api_instance.controler, response["items"])
        queue.put(response)

    def download_metadata(self, page: str, queue: Queue) -> None:
        """Download and store one page returned by the metadata export."""
        response = self.process_progress(page=page)
        (
            _threaded_items,
            metadata_upserts,
            metadata_errors,
        ) = self._backend.store_metadata(response["items"])
        self.metadata_count_upserts += metadata_upserts
        self.metadata_count_errors += metadata_errors
        queue.put(response)

    def delete(self, page: str, queue: Queue) -> None:
        """
        Delete (or not) data in DB from a page download

        Args:
            page (str): url to download
            queue (Queue): gather the progress
        """
        response = self.process_progress(page=page)

        if response.get("total_len") > 0:
            self.data_count_delete += self._backend.delete_data(response.get("items"))
            logger.info(
                "%s data have been deleted from %s", str(self.data_count_delete), self._config.name
            )
            queue.put(response)
        else:
            logger.info(
                _("No new deleted data from %(source)s %(controler)s"),
                {"source": self._config.name, "controler": self._api_instance.controler},
            )

    def process_progress(self, page: str) -> dict:
        """
        Compute the progress of the task

        Args:
            page (str): url to download

        Returns:
            dict (dict): dict containing items, len_items, total_len
        """
        resp = self._api_instance.get_page(page)
        items = resp["items"]
        len_items = len(items)
        return {
            "items": items,
            "len_items": len_items,
            "total_len": resp["total_filtered"] if "total_filtered" in resp else resp["total"],
        }

    def store(self) -> None:
        """Store data into Database"""
        if self._config.data_type in (
            "metadata_only",
            "synthese_with_metadata_separated",
        ):
            if not self.store_metadata(xfer_type="full"):
                return
            if self._config.data_type == "metadata_only":
                self.xfer_status = XferStatus.success
                return

        # Store start download TimeStamp to populate increment log  after download end.

        params = {"limit": self._config.max_page_length}
        logger.debug(_("Getting items from controler %s"), self._api_instance.controler)
        # logger.info(self._config._query_strings)
        params.update(self._config.query_strings)
        logger.info(_("QueryStrings %s"), params)
        pages = None
        try:
            pages, data_count_items, _xfer_http_status = self._api_instance.page_list(
                kind="data", params=params
            )
            self.api_count_items += data_count_items
        except (RetryError, ResponseError) as e:
            self.xfer_status = XferStatus.failed
            self.xfer_comment = str(e)
            logger.critical("%s %s %s", e, e.response, dir(e))
            logger.error(_("Could not retrieve API data from source %s"), self._config.name)
            return

        try:
            # input(f"FULL DOWNLOAD INPUT {self._config.name}")
            if pages:
                self.xfer_status = XferStatus.import_data
                self.xfer_type = "full"
                self.xfer_filters = (json.dumps(params, default=str),)
                self._backend.import_log(
                    controler=self._api_instance.controler,
                    values={
                        "xfer_type": self.xfer_type,
                        "xfer_status": self.xfer_status,
                        "xfer_filters": self.xfer_filters,
                    },
                )

                self.launch_threads(
                    nb_threads=self._config.nb_threads, func=self.download, pages=pages
                )
                self.xfer_status = XferStatus.success
                # Log download timestamp to download.

        except (RetryError, ResponseError) as e:
            self.queue.put(("EXIT"))
            self.xfer_status = XferStatus.failed
            self.xfer_comment = str(e)
            logger.error(
                "A problem occured on FULL DOWNLOAD process for source %s : %s",
                self._config.name,
                e,
            )
            return

        self.xfer_status = XferStatus.success

    def store_metadata(self, xfer_type: str) -> bool:
        """Fully refresh metadata from its dedicated export."""
        params = {"limit": self._config.max_page_length}
        logger.info(_("Getting metadata from source %s"), self._config.name)
        try:
            pages, metadata_count_items, _xfer_http_status = self._api_instance.page_list(
                kind="metadata", params=params
            )
            self.api_count_items += metadata_count_items
            self.xfer_type = xfer_type
            self.xfer_status = XferStatus.import_data
            self._backend.import_log(
                controler=self._api_instance.controler,
                values={
                    "xfer_type": xfer_type,
                    "xfer_status": self.xfer_status,
                    "xfer_filters": (json.dumps(params, default=str),),
                },
            )
            if pages:
                errors = self.launch_threads(
                    nb_threads=self._config.nb_threads,
                    func=self.download_metadata,
                    pages=pages,
                )
                if errors:
                    raise errors[0]
        except (RetryError, ResponseError) as error:
            self.queue.put(("EXIT"))
            self.xfer_status = XferStatus.failed
            self.xfer_comment = str(error)
            logger.error(
                _(
                    "A problem occured while downloading metadata from source "
                    "%(source)s: %(error)s"
                ),
                {"source": self._config.name, "error": error},
            )
            return False
        return True

    def update(self, since: Optional[str] = None, actions: Optional[list] = None) -> None:
        """[summary]

        Args:
            since (str): DateTime limit to update.
            actions (list): Actions list (Insert > I, Update > U, Delete > D)
        """

        if self._config.data_type == "metadata_only":
            if not self.store_metadata(xfer_type="update"):
                return
            self.xfer_status = XferStatus.success
            return

        # Update new or modified data from API
        logger.debug(_("Updating items from controler %s"), self._api_instance.controler)
        # Get last update from increment log.

        if actions is None:
            actions = ["I", "U"]
        params = {"action": actions}

        if since is None:
            since = self._backend.import_get(self._api_instance.controler)
            if since is None:
                logger.warning(
                    _(
                        "No download exists in the import table for source %s, "
                        "a complete download will be launched"
                    ),
                    self._config.std_name,
                )
                self.store()
                return

        # A separated metadata refresh must finish before observation upserts.
        if self._config.data_type == "synthese_with_metadata_separated":
            if not self.store_metadata(xfer_type="update"):
                return

        params["limit"] = self._config.max_page_length
        params["filter_d_up_derniere_action"] = since
        params.update(self._config.query_strings)
        logger.info(_("QueryStrings %s"), params)

        logger.info(
            _("Getting new or update data from source %(source)s since %(since)s"),
            {"source": self._config.name, "since": since},
        )

        # Process UPDATE
        try:
            upsert_pages, data_count_items, _xfer_http_status = self._api_instance.page_list(
                kind="data", params=params
            )
            self.api_count_items += data_count_items
            self.xfer_type = "update"
            self.xfer_status = XferStatus.import_data
            self.xfer_filters = (json.dumps(params, default=str),)

            self._backend.import_log(
                controler=self._api_instance.controler,
                values={
                    "xfer_type": "update",
                    "xfer_status": self.xfer_status,
                    "xfer_filters": self.xfer_filters,
                },
            )
            # input(f"UPDATE INPUT {self._config.name}")
            if upsert_pages:
                self.launch_threads(
                    nb_threads=self._config.nb_threads,
                    func=self.download,
                    pages=upsert_pages,
                )

        except (RetryError, ResponseError) as e:
            self.queue.put(("EXIT"))
            logger.critical("%s %s %s %s", dir(e), type(e), e.args, str(e))
            self.xfer_status = XferStatus.failed
            self.xfer_comment = str(e)
            logger.error(
                _("A problem occured on UPDATE process for source %(source)s: %(error)s"),
                {"source": self._config.name, "error": e},
            )
            return
        # Process DELETE
        logger.info(
            _("Getting deleted data from source %(source)s since %(since)s"),
            {"source": self._config.name, "since": since},
        )
        try:
            deleted_pages, _total_len, _xfer_http_status = self._api_instance.page_list(
                kind="log",
                params={
                    "meta_last_action_date": f"gte:{since}",
                    "limit": self._config.max_page_length,
                    "last_action": "D",
                },
                pagination_param="page",
            )
            # input(f"DELETE INPUT {self._config.name}")
            self.xfer_status = XferStatus.delete
            self._backend.import_log(
                controler=self._api_instance.controler,
                values={
                    "xfer_status": self.xfer_status,
                },
            )
            if deleted_pages:
                self.launch_threads(
                    nb_threads=self._config.nb_threads,
                    func=self.delete,
                    pages=deleted_pages,
                    store=False,
                )

        except (RetryError, ResponseError) as e:
            self.queue.put(("EXIT"))
            self.xfer_status = XferStatus.failed
            self.xfer_comment = str(e)
            logger.error(
                "A problem occured on DELETE process for source %s : %s", self._config.name, e
            )
            return

        self.xfer_status = XferStatus.success

    def exit(self):
        """Final log on exit"""
        self._backend.import_log(
            controler=self._api_instance.controler,
            values={
                "xfer_end_ts": datetime.now(),
                "api_count_items": self.api_count_items,
                "api_count_errors": self.api_count_errors,
                "data_count_upserts": self.data_count_upserts,
                "data_count_delete": self.data_count_delete,
                "data_count_errors": self.data_count_errors,
                "metadata_count_upserts": self.metadata_count_upserts,
                "metadata_count_errors": self.metadata_count_errors,
                "xfer_status": self.xfer_status,
                "comment": self.xfer_comment,
            },
        )


class Data(DownloadGn):
    """Implement store from observations controler.

    Methods
    - store               - Download by page and store to json

    """

    def __init__(self, config, backend):
        try:
            super().__init__(config, DataAPI(config), backend)
        except (HTTPError, ExportModuleNotFoundError, InvalidSchema) as e:
            logger.critical(e)

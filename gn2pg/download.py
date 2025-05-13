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

from requests.exceptions import RetryError

from gn2pg import _, __version__
from gn2pg.api import DataAPI
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

        self._limits = {
            "max_retry": max_retry,
            "max_requests": max_requests,
        }

        # Init import log
        self.import_log_id = self._backend.import_log(
            controler=self._api_instance.controler,
            values={"xfer_status": XferStatus.init, "xfer_start_ts": datetime.now()},
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
                            _("%s %d datas (%d/%d %.2f %%) from %s %s"),
                            msg,
                            response["len_items"],
                            progress,
                            response["total_len"],
                            perc_progress,
                            self._config.name,
                            self._api_instance.controler,
                        )
            except Exception as e:  # pylint: disable=W0718
                errors.append(e)
                self.api_count_errors += 1

        # The Queue enables the report thread to get the progress from other threads
        self.queue: Queue = Queue()
        errors: List[Exception] = []
        # Initialize and start the report thread
        thread = Thread(target=report, args=[self.queue])
        thread.start()
        # Start the worker threads
        with ThreadPool(nb_threads) as thread:
            thread.map(partial(func, queue=self.queue), pages)
        # Will stop the report thread
        # self._backend.import_log(
        #     controler=self._api_instance.controler,
        #     id=self.import_log_id,
        #     values={
        #         "xfer_end_ts": datetime.now(),
        #         "api_count_items": self.api_count_items,
        #         "api_count_errors": self.api_count_errors,
        #         "data_count_upserts": self.data_count_upserts,
        #         "data_count_delete": self.data_count_delete,
        #         "data_count_errors": self.data_count_errors,
        #         "metadata_count_upserts": self.metadata_count_upserts,
        #         "metadata_count_errors": self.metadata_count_errors,
        #         "xfer_status": "success",
        #     },
        # )
        self.queue.put(("DONE"))
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
                _("No new deleted data from %s %s"),
                self._config.name,
                self._api_instance.controler,
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
        # Store start download TimeStamp to populate increment log  after download end.

        params = {"limit": self._config.max_page_length}
        logger.debug(_("Getting items from controler %s"), self._api_instance.controler)
        # logger.info(self._config._query_strings)
        params.update(self._config.query_strings)
        logger.info(_("QueryStrings %s"), params)
        pages = None
        try:
            pages, self.api_count_items, status_code = self._api_instance.page_list(
                kind="data", params=params
            )
        except RetryError:
            logger.error(_("Could not retrieve API data from source %s"), self._config.name)
            return

        try:
            # input(f"FULL DOWNLOAD INPUT {self._config.name}")
            if pages:
                self._backend.import_log(
                    controler=self._api_instance.controler,
                    values={
                        "xfer_type": "full",
                        "xfer_status": XferStatus.import_data,
                        "xfer_http_status": status_code,
                        "xfer_filters": json.dumps(params),
                    },
                )

                self.launch_threads(
                    nb_threads=self._config.nb_threads, func=self.download, pages=pages
                )

                # Log download timestamp to download.

        except RetryError as e:
            self.queue.put(("EXIT"))
            logger.error(
                "A problem occured on FULL DOWNLOAD process for source %s : %s",
                self._config.name,
                e,
            )
            return

        return

    def update(self, since: Optional[str] = None, actions: Optional[list] = None) -> None:
        """[summary]

        Args:
            since (str): DateTime limit to update.
            actions (list): Actions list (Insert > I, Update > U, Delete > D)
        """

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

        params["limit"] = self._config.max_page_length
        params["filter_d_up_derniere_action"] = since
        params.update(self._config.query_strings)
        logger.info(_("QueryStrings %s"), params)

        logger.info(
            _("Getting new or update data from source %s since %s"),
            self._config.name,
            since,
        )

        # Process UPDATE
        try:
            upsert_pages, self.api_count_items, status_code = self._api_instance.page_list(
                kind="data", params=params
            )
            self._backend.import_log(
                controler=self._api_instance.controler,
                values={
                    "xfer_type": "update",
                    "xfer_status": XferStatus.import_data,
                    "xfer_http_status": status_code,
                    "xfer_filters": json.dumps(params, default=str),
                },
            )
            # input(f"UPDATE INPUT {self._config.name}")
            if upsert_pages:
                self.launch_threads(
                    nb_threads=self._config.nb_threads,
                    func=self.download,
                    pages=upsert_pages,
                )
        except RetryError as e:
            self.queue.put(("EXIT"))
            logger.error(
                "A problem occured on UPDATE process for source %s : %s", self._config.name, e
            )
            return
        # Process DELETE
        logger.info(
            _("Getting deleted data from source %s since %s"),
            self._config.name,
            since,
        )
        try:
            deleted_pages, _total_len, status_code = self._api_instance.page_list(
                kind="log",
                params={
                    "meta_last_action_date": f"gte:{since}",
                    "limit": self._config.max_page_length,
                    "last_action": "D",
                },
                pagination_param="page",
            )
            # input(f"DELETE INPUT {self._config.name}")
            self._backend.import_log(
                controler=self._api_instance.controler,
                values={"xfer_status": XferStatus.delete, "xfer_http_status": status_code},
            )
            if deleted_pages:

                self.launch_threads(
                    nb_threads=self._config.nb_threads,
                    func=self.delete,
                    pages=deleted_pages,
                    store=False,
                )
        except RetryError as e:
            self.queue.put(("EXIT"))
            logger.error(
                "A problem occured on DELETE process for source %s : %s", self._config.name, e
            )
            return

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
                "xfer_status": XferStatus.success,
            },
        )


class Data(DownloadGn):
    """Implement store from observations controler.

    Methods
    - store               - Download by page and store to json

    """

    def __init__(self, config, backend):
        super().__init__(config, DataAPI(config), backend)

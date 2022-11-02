"""Methods to download from VisioNature and store to file.


Methods

- download_taxo_groups      - Download and store taxo groups

Properties

-

"""
from typing import Callable

from functools import partial
import logging
from datetime import datetime
from multiprocessing import Queue
from multiprocessing.pool import ThreadPool
from threading import Thread

from . import _, __version__
from .api import DataAPI, DatasetsAPI

logger = logging.getLogger("transfer_gn.download_gn")


class DownloadGnException(Exception):
    """An exception occurred while handling download or store."""


class NotImplementedException(DownloadGnException):
    """Feature not implemented."""


class DownloadGn:
    """Top class, not for direct use.
    Provides internal and template methods."""

    def __init__(
        self, config, api_instance, backend, max_retry=None, max_requests=None
    ) -> None:
        self._config = config
        self._api_instance = api_instance
        self._backend = backend
        if max_retry is None:
            max_retry = config.max_retry
        if max_requests is None:
            max_requests = config.max_requests
        self._limits = {
            "max_retry": max_retry,
            "max_requests": max_requests,
        }

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
    def launch_treads(self, nb_threads: int, func: Callable, pages: list, store=True):
        """
        Launch 1 + nb_threads threads to execute a function func on a list of pages

        Args:
            nb_threads (int): number of threads to compute the function on the pages
            func (Callable): function that each thread will call
            pages (list): list of pages
            store (bool): if True, display Storing in logger
        
        Returns:
            None
        """
        def report(queue):
            """
            From a Queue, get the progress, increase it and log it
            """
            progress = 0
            while True:
                response = queue.get()
                if response == "DONE":
                    break
                progress += response['len_items']
                perc_progress = round(progress/response['total_len']*100,2)
                if response.get("total_len", 0) > 0:
                    msg = "Storing" if store else "Deleting"
                    logger.info("%s %d datas (%d/%d %.2f %%) from %s %s", msg, response['len_items'], progress, response['total_len'], perc_progress, self._config.name, self._api_instance.controler)

        # The Queue enables the report thread to get the progress from other threads
        q = Queue()
        # Initialize and start the report thread
        thread = Thread(target=report, args=[q])
        thread.start()
        # Start the worker threads 
        with ThreadPool(nb_threads) as thread:
            thread.map(partial(func, queue=q), pages)
        # Will stop the report thread
        q.put(("DONE"))

    def download(self, page, queue):
        """
        Download a page and store the progress in the provided queue
        """
        response = self.process_progress(page=page)

        self._backend.store_data(
            self._api_instance.controler, response["items"]
        )
        queue.put(response)

    def delete(self, page, queue):
        """
        Delete (or not) data in DB from a page download

        Args:
            page (str): url to download
            progress (int): 
        """
        response = self.process_progress(page=page)

        if response.get("total_len") > 0:
            self._backend.store_data(
                self._backend.delete_data(response.get("items"))
            )
            queue.put(response)
        else:
            logger.info(
                f"No new deleted data from {self._config.name} {self._api_instance.controler}"
            )

    def process_progress(self, page):
        resp = self._api_instance.get_page(page)
        items = resp["items"]
        len_items = len(items)
        return {
            "items": items,
            "len_items": len_items,
            "total_len": resp["total_filtered"],
        }

    def store(self) -> None:
        """Store data into Database

        Returns:
            None
        """
        # Store start download TimeStamp to populate increment log  after download end.

        increment_ts = datetime.now()
        params = {"limit": self._config.max_page_length}
        logger.debug(
            _(f"Getting items from controler {self._api_instance.controler}")
        )
        # logger.info(self._config._query_strings)
        params.update(self._config.query_strings)
        logger.info(f"QueryStrings  {params}")
        pages = self._api_instance._page_list(kind="data", params=params)
        self._backend.download_log(
            self._api_instance.controler,
            self._api_instance.transfer_errors,
            self._api_instance.http_status,
        )

        self.launch_treads(nb_threads=self._config.nb_threads, func=self.download, pages=pages)

        # Log download timestamp to download.
        self._backend.increment_log(
            controler=self._api_instance.controler, last_ts=increment_ts
        )

    def update(
        self, since: str = None, actions: list = ["I", "U"]
    ) -> None:
        """[summary]

        Args:
            since (str): DateTime limit to update.

        Returns:
            [type]: [description]
        """
        # Update new or modified data from API
        logger.debug(
            _(f"Updating items from controler {self._api_instance.controler}")
        )
        # Get last update from increment log.
        increment_ts = datetime.now()

        params = {"action": actions}

        if since is None:
            since = (
                self._backend.increment_get(self._api_instance.controler)
                if self._backend.increment_get(self._api_instance.controler)
                is not None
                else self._backend.download_get(self._api_instance.controler)
            )

        params["limit"] = self._config.max_page_length
        params["filter_d_up_derniere_action"] = since
        params.update(self._config.query_strings)
        logger.info(f"QueryStrings  {params}")

        logger.info(
            _(
                f"Getting new or update data from source {self._config.source} since {since}"
            )
        )

        upsert_pages = self._api_instance._page_list(
            kind="data", params=params
        )

        if upsert_pages is not None:
            self.launch_treads(nb_threads=self._config.nb_threads, func=self.download, pages=upsert_pages)

        # Delete data deleted from source
        logger.info(
            _(
                f"Preparing data delete from source {self._config.name} since {since}"
            )
        )

        deleted_pages = self._api_instance._page_list(
            kind="log",
            params={
                "filter_d_up_meta_last_action_date": since,
                "limit": self._config.max_page_length,
                "last_action": "D",
            },
        )

        if deleted_pages:
            self.launch_treads(nb_threads=self._config.nb_threads, func=self.delete, pages=deleted_pages)

        self._backend.increment_log(
            controler=self._api_instance.controler, last_ts=increment_ts
        )

        return None


class Data(DownloadGn):
    """Implement store from observations controler.

    Methods
    - store               - Download by page and store to json

    """

    def __init__(self, config, backend, max_retry=None, max_requests=None):
        super().__init__(
            config, DataAPI(config), backend, max_retry, max_requests
        )
        return None


class Datasets(DownloadGn):
    """Implement store from places controler.

    Methods
    - store               - Download and store to json

    """

    def __init__(self, config, backend, max_retry=None, max_requests=None):
        super().__init__(
            config, DatasetsAPI(config), backend, max_retry, max_requests
        )
        return None

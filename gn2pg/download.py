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

from requests.exceptions import HTTPError, InvalidSchema, RequestException
from urllib3.exceptions import ResponseError

from gn2pg import _, __version__
from gn2pg.api import APIException, DataAPI, ExportModuleNotFoundError
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
        ) = self._backend.store_data(
            self._api_instance.controler,
            response["items"],
            id_key_name=self._config.id_key_name,
            uuid_key_name=self._config.uuid_key_name,
        )
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

    def delete(self, page: dict, queue: Queue) -> None:
        """
        Delete (or not) data in DB from a page download

        Args:
            page (dict): durable page checkpoint containing its URL
            queue (Queue): gather the progress
        """
        self._backend.start_download_page(page["id"])
        try:
            response = self.process_progress(page=page["url"])

            if response.get("total_len") > 0:
                self.data_count_delete += self._backend.delete_data(response.get("items"))
                logger.info(
                    "%s data have been deleted from %s",
                    str(self.data_count_delete),
                    self._config.name,
                )
                queue.put(response)
            else:
                logger.info(
                    _("No new deleted data from %(source)s %(controler)s"),
                    {"source": self._config.name, "controler": self._api_instance.controler},
                )
            self._backend.finish_download_page(page["id"], item_count=response["len_items"])
        except Exception as error:  # pylint: disable=broad-exception-caught
            self._backend.finish_download_page(page["id"], error=str(error))
            raise DownloadGnException(f"Delete page {page['page_number']} failed") from error

    def resume_delete(self) -> bool:
        """Resume the latest incomplete delete phase without replaying data upserts."""
        resume = self._backend.resumable_delete_pages(self._api_instance.controler)
        if resume is None:
            return False

        logger.info(_("Resuming an incomplete delete phase for source %s"), self._config.name)
        self.xfer_type = "update"
        self.xfer_status = XferStatus.delete
        self.xfer_filters = {"resume": "delete"}
        self._backend.import_log(
            controler=self._api_instance.controler,
            values={
                "xfer_start_ts": resume["xfer_start_ts"],
                "xfer_type": self.xfer_type,
                "xfer_status": self.xfer_status,
                "xfer_filters": self.xfer_filters,
            },
        )
        try:
            if resume.get("rebuild"):
                filters = resume["xfer_filters"]
                if not self._process_deletes(
                    filters["filter_d_up_derniere_action"],
                    filters["filter_d_lo_derniere_action"],
                ):
                    raise DownloadGnException("Could not rebuild the bounded delete phase")
            elif resume["pages"]:
                self.launch_threads(
                    nb_threads=self._config.nb_threads,
                    func=self.delete,
                    pages=resume["pages"],
                    store=False,
                )
        except DownloadGnException as error:
            self.xfer_status = XferStatus.failed
            self.xfer_comment = str(error)
            logger.error(
                _("Could not resume deleted data for source %(source)s: %(error)s"),
                {"source": self._config.name, "error": error},
            )
        else:
            self._backend.complete_resumed_delete(resume["import_id"])
            self.xfer_status = XferStatus.success
        return True

    def resume_update(self) -> bool:
        """Resume an interrupted update phase before starting a new window."""
        if self.resume_delete():
            return True
        resume = self._resumable_cursor("update")
        if resume is None:
            return False
        resume_params = resume["xfer_filters"]
        if self._execute_cursor_transfer(
            resume_params,
            "update",
            last_cursor=resume["cursor_value"],
            start_ts=resume["xfer_start_ts"],
            resumed_import_id=resume["id"],
        ) and self._process_deletes(
            resume_params["filter_d_up_derniere_action"],
            resume_params["filter_d_lo_derniere_action"],
        ):
            self.xfer_status = XferStatus.success
        return True

    def _refresh_update_metadata(self) -> bool:
        """Refresh separated metadata when required by the source type."""
        if self._config.data_type == "synthese_with_metadata_separated":
            return self.store_metadata(xfer_type="update")
        return True

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

    @property
    def uses_cursor(self) -> bool:
        """Return whether this source uses stable numeric keyset pagination."""
        return getattr(self._config, "pagination_strategy", "offset") == "cursor"

    def _download_by_cursor(self, params: dict, last_cursor: Optional[int] = None) -> None:
        """Download and commit data pages while advancing a numeric cursor."""
        cursor_column = self._config.id_key_name
        cursor_filter = f"filter_n_up_{cursor_column}"
        if last_cursor is None and "filter_d_up_derniere_action" in params:
            next_cursor = None
        else:
            configured_start = int(params.get(cursor_filter, self._config.cursor_start))
            next_cursor = max(
                configured_start,
                configured_start if last_cursor is None else int(last_cursor) + 1,
            )
        limit = self._config.max_page_length
        progress = 0
        total_items = None

        while True:
            page_params = dict(params)
            page_params["orderby"] = f"{cursor_column}:ASC"
            if next_cursor is None:
                page_params.pop(cursor_filter, None)
            else:
                page_params[cursor_filter] = next_cursor
            response = self._api_instance.get_cursor_page(page_params)
            items = response["items"]
            effective_limit = response.get("limit", limit)

            if total_items is None:
                total_items = response.get("total_filtered", response.get("total", len(items)))
                self.api_count_items += total_items
            if not items:
                break

            page_cursor = self._validated_page_cursor(items, cursor_column, next_cursor)

            self._store_cursor_page(items)
            self._backend.save_cursor(cursor_column, page_cursor)
            progress += len(items)

            logger.info(
                _(
                    "Stores %(item_count)d datas "
                    "(%(progress)d/%(total)d %(percentage).2f %%) from "
                    "%(source)s %(controler)s; cursor %(column)s=%(cursor)d"
                ),
                {
                    "item_count": len(items),
                    "progress": progress,
                    "total": total_items,
                    "percentage": (
                        round(progress / total_items * 100, 2) if total_items else 100.0
                    ),
                    "column": cursor_column,
                    "cursor": page_cursor,
                    "source": self._config.name,
                    "controler": self._api_instance.controler,
                },
            )
            next_cursor = page_cursor + 1
            if len(items) < effective_limit:
                break

    def _store_cursor_page(self, items: list[dict]) -> None:
        """Store a cursor page and update the transfer counters."""
        result = self._backend.store_data(
            self._api_instance.controler,
            items,
            id_key_name=self._config.id_key_name,
            uuid_key_name=self._config.uuid_key_name,
        )
        (
            self.data_count_upserts,
            self.data_count_errors,
            self.metadata_count_upserts,
            self.metadata_count_errors,
        ) = result[1:]

    @staticmethod
    def _validated_page_cursor(items: list[dict], column: str, minimum: Optional[int]) -> int:
        """Return the last cursor after validating numeric, unique ordering."""
        try:
            values = [int(item[column]) for item in items]
        except (KeyError, TypeError, ValueError) as error:
            raise DownloadGnException(
                f"Cursor column {column!r} is missing or not numeric"
            ) from error
        if values != sorted(values) or len(values) != len(set(values)):
            raise DownloadGnException(f"Cursor column {column!r} is not uniquely ordered")
        if minimum is not None and values[-1] < minimum:
            raise DownloadGnException(f"Cursor {column!r} did not advance beyond {minimum}")
        return values[-1]

    def _execute_cursor_transfer(
        self,
        params: dict,
        xfer_type: str,
        *,
        last_cursor: Optional[int] = None,
        start_ts: Optional[datetime] = None,
        resumed_import_id: Optional[int] = None,
    ) -> bool:
        """Run or resume a cursor transfer and persist its lifecycle."""
        self.xfer_type = xfer_type
        self.xfer_status = XferStatus.import_data
        self.xfer_filters = dict(params)
        values = {
            "xfer_type": xfer_type,
            "xfer_status": self.xfer_status,
            "xfer_filters": self.xfer_filters,
            "cursor_phase": "data",
            "cursor_column": self._config.id_key_name,
            "cursor_value": last_cursor,
        }
        if start_ts is not None:
            values["xfer_start_ts"] = start_ts
        self._backend.import_log(controler=self._api_instance.controler, values=values)
        if resumed_import_id is not None:
            self._backend.supersede_cursor(resumed_import_id)
        try:
            self._download_by_cursor(params, last_cursor=last_cursor)
        except Exception as error:  # pylint: disable=broad-exception-caught
            self.xfer_status = XferStatus.failed
            self.xfer_comment = str(error)
            logger.error(
                _("Cursor download failed for source %(source)s: %(error)s"),
                {"source": self._config.name, "error": error},
            )
            return False
        self._backend.complete_cursor()
        return True

    def _resumable_cursor(self, xfer_type: Optional[str]) -> Optional[dict]:
        """Return a claimed cursor checkpoint when cursor mode is enabled."""
        if not self.uses_cursor:
            return None
        return self._backend.resumable_cursor(self._api_instance.controler, xfer_type)

    def retry_failed(self) -> bool:
        """Resume the latest checkpointed API failure without starting a new transfer."""
        if self.resume_delete():
            return self.xfer_status == XferStatus.success

        resume = self._resumable_cursor(None)
        if resume is None:
            self.xfer_status = XferStatus.skipped
            logger.info(_("No failed download can be resumed for source %s"), self._config.name)
            return False

        if resume["cursor_column"] != self._config.id_key_name:
            self.xfer_status = XferStatus.failed
            self.xfer_comment = _(
                "The failed download cursor does not match the configured id_key_name"
            )
            logger.error("%s: %s", self._config.name, self.xfer_comment)
            return False

        xfer_type = resume["xfer_type"]
        params = resume["xfer_filters"]
        succeeded = self._execute_cursor_transfer(
            params,
            xfer_type,
            last_cursor=resume["cursor_value"],
            start_ts=resume["xfer_start_ts"],
            resumed_import_id=resume["id"],
        )
        if succeeded and xfer_type == "update":
            succeeded = self._process_deletes(
                params["filter_d_up_derniere_action"],
                params["filter_d_lo_derniere_action"],
            )
        if succeeded:
            self.xfer_status = XferStatus.success
        return succeeded

    def store(self) -> None:
        """Store data into Database"""
        # Bound the full export before making any request so that new data
        # arriving during offset pagination cannot extend the result set.
        until = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if self._config.data_type != "metadata_only":
            resume = self._resumable_cursor("full")
            if resume is not None:
                if self._execute_cursor_transfer(
                    resume["xfer_filters"],
                    "full",
                    last_cursor=resume["cursor_value"],
                    start_ts=resume["xfer_start_ts"],
                    resumed_import_id=resume["id"],
                ):
                    self.xfer_status = XferStatus.success
                return

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

        params = dict(self._config.query_strings)
        params["limit"] = self._config.max_page_length
        params["filter_d_lo_derniere_action"] = until
        logger.debug(_("Getting items from controler %s"), self._api_instance.controler)
        logger.info(_("QueryStrings %s"), params)
        if self.uses_cursor:
            if self._execute_cursor_transfer(params, "full"):
                self.xfer_status = XferStatus.success
            return
        pages = None
        try:
            pages, data_count_items, _xfer_http_status = self._api_instance.page_list(
                kind="data", params=params
            )
            self.api_count_items += data_count_items
        except (RequestException, ResponseError, APIException) as e:
            self.xfer_status = XferStatus.failed
            self.xfer_comment = str(e)
            logger.critical("%s", e)
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

        except (RequestException, ResponseError, APIException) as e:
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
        except (RequestException, ResponseError, APIException) as error:
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
            if self.store_metadata(xfer_type="update"):
                self.xfer_status = XferStatus.success
            return

        # Freeze the upper end of the incremental window before making any
        # export request. All offset pages therefore address the same bounded
        # period, even when the source keeps receiving new observations.
        until = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if since is None and self.resume_update():
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
        if not self._refresh_update_metadata():
            return

        params.update(self._config.query_strings)
        params["limit"] = self._config.max_page_length
        params["filter_d_up_derniere_action"] = since
        params["filter_d_lo_derniere_action"] = until
        logger.info(_("QueryStrings %s"), params)

        logger.info(
            _("Getting new or update data from source %(source)s since %(since)s"),
            {"source": self._config.name, "since": since},
        )

        if self.uses_cursor:
            if self._execute_cursor_transfer(params, "update") and self._process_deletes(
                since, until
            ):
                self.xfer_status = XferStatus.success
            return

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

        except (RequestException, ResponseError, APIException) as e:
            self.queue.put(("EXIT"))
            logger.critical("%s %s %s %s", dir(e), type(e), e.args, str(e))
            self.xfer_status = XferStatus.failed
            self.xfer_comment = str(e)
            logger.error(
                _("A problem occured on UPDATE process for source %(source)s: %(error)s"),
                {"source": self._config.name, "error": e},
            )
            return
        if self._process_deletes(since, until):
            self.xfer_status = XferStatus.success

    def _process_deletes(self, since: str, until: str) -> bool:
        """Download and apply the bounded deletion phase of an update."""
        logger.info(
            _("Getting deleted data from source %(source)s since %(since)s"),
            {"source": self._config.name, "since": since},
        )
        try:
            delete_params = {
                "meta_last_action_date": [f"gte:{since}", f"lte:{until}"],
                "limit": self._config.max_page_length,
                "last_action": "D",
                "sort": "meta_last_action_date:asc",
            }
            deleted_pages, _total_len, _xfer_http_status = self._api_instance.page_list(
                kind="log",
                params=delete_params,
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
                durable_pages = self._backend.create_download_pages("delete", deleted_pages)
                self.launch_threads(
                    nb_threads=self._config.nb_threads,
                    func=self.delete,
                    pages=durable_pages,
                    store=False,
                )

        except (RequestException, ResponseError, APIException, DownloadGnException) as e:
            self.queue.put(("EXIT"))
            self.xfer_status = XferStatus.failed
            self.xfer_comment = str(e)
            logger.error(
                "A problem occured on DELETE process for source %s : %s", self._config.name, e
            )
            return False
        return True

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

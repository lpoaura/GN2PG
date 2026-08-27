"""Test download"""

import datetime
from types import SimpleNamespace

import pytest

from gn2pg.download import DownloadGn


class TestDownload:
    """Test download"""

    def test_store(self, data, caplog):
        """Test store"""
        data.store()
        now = datetime.datetime.now()
        increment = data._backend.import_get(data._api_instance.controler)

        assert now.strftime("%d/%m/%Y %H") == increment.strftime("%d/%m/%Y %H")
        assert "items have been stored in db from" in caplog.text
        assert "100.00 %" in caplog.text


def test_launch_threads_stops_reporter_when_worker_fails():
    downloader = object.__new__(DownloadGn)
    downloader._config = SimpleNamespace(name="Source")
    downloader._api_instance = SimpleNamespace(controler="data")
    downloader.api_count_errors = 0

    def fail(page, queue):
        raise RuntimeError(page)

    with pytest.raises(RuntimeError, match="page-1"):
        downloader.launch_threads(nb_threads=1, func=fail, pages=["page-1"])


def test_update_bounds_export_with_a_frozen_upper_timestamp(monkeypatch):
    class FrozenDateTime:
        @staticmethod
        def now():
            return datetime.datetime(2026, 8, 27, 14, 30, 45)

    calls = []
    downloader = object.__new__(DownloadGn)
    downloader._config = SimpleNamespace(
        data_type="synthese",
        max_page_length=100,
        query_strings={"filter_d_lo_derniere_action": "unsafe-override"},
        name="Source",
        nb_threads=1,
    )
    downloader._api_instance = SimpleNamespace(
        controler="data",
        page_list=lambda **kwargs: calls.append(kwargs) or (None, 0, 200),
    )
    downloader._backend = SimpleNamespace(import_log=lambda **kwargs: None)
    downloader.api_count_items = 0
    downloader.xfer_filters = {}
    downloader.xfer_status = None
    downloader.xfer_type = ""
    downloader.queue = SimpleNamespace(put=lambda value: None)
    monkeypatch.setattr("gn2pg.download.datetime", FrozenDateTime)

    downloader.update(since="2026-08-26 00:00:00")

    export_params = calls[0]["params"]
    assert export_params["filter_d_up_derniere_action"] == "2026-08-26 00:00:00"
    assert export_params["filter_d_lo_derniere_action"] == "2026-08-27 14:30:45"


def test_full_download_bounds_export_with_a_frozen_upper_timestamp(monkeypatch):
    class FrozenDateTime:
        @staticmethod
        def now():
            return datetime.datetime(2026, 8, 27, 14, 30, 45)

    calls = []
    downloader = object.__new__(DownloadGn)
    downloader._config = SimpleNamespace(
        data_type="synthese",
        max_page_length=100,
        query_strings={"filter_d_lo_derniere_action": "unsafe-override"},
        name="Source",
        nb_threads=1,
    )
    downloader._api_instance = SimpleNamespace(
        controler="data",
        page_list=lambda **kwargs: calls.append(kwargs) or (None, 0, 200),
    )
    downloader._backend = SimpleNamespace(import_log=lambda **kwargs: None)
    downloader.api_count_items = 0
    downloader.xfer_filters = {}
    downloader.xfer_status = None
    downloader.xfer_type = ""
    monkeypatch.setattr("gn2pg.download.datetime", FrozenDateTime)

    downloader.store()

    export_params = calls[0]["params"]
    assert export_params["limit"] == 100
    assert export_params["filter_d_lo_derniere_action"] == "2026-08-27 14:30:45"

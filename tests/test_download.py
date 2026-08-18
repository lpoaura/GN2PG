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

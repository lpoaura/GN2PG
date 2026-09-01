"""Test download"""

import datetime
import logging
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
    downloader._backend = SimpleNamespace(
        import_log=lambda **kwargs: None,
        resumable_delete_pages=lambda controler: None,
    )
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
    delete_params = calls[1]["params"]
    assert delete_params["meta_last_action_date"] == [
        "gte:2026-08-26 00:00:00",
        "lte:2026-08-27 14:30:45",
    ]
    assert delete_params["sort"] == "meta_last_action_date:asc"


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


def test_update_resumes_delete_pages_without_replaying_upserts():
    resumed_pages = [{"id": 7, "page_number": 3, "url": "https://example.test/log?page=3"}]
    import_updates = []
    completed_runs = []
    downloader = object.__new__(DownloadGn)
    downloader._config = SimpleNamespace(
        data_type="synthese",
        name="Source",
        nb_threads=1,
    )
    downloader._api_instance = SimpleNamespace(
        controler="data",
        page_list=lambda **kwargs: pytest.fail(
            "upserts must not be requested during delete resume"
        ),
    )
    downloader._backend = SimpleNamespace(
        resumable_delete_pages=lambda controler: {
            "import_id": 41,
            "xfer_start_ts": datetime.datetime(2026, 8, 26, 12, 0, 0),
            "pages": resumed_pages,
        },
        import_log=lambda **kwargs: import_updates.append(kwargs),
        complete_resumed_delete=lambda import_id: completed_runs.append(import_id),
    )
    downloader.launch_threads = lambda **kwargs: resumed_pages.clear()
    downloader.xfer_filters = {}
    downloader.xfer_status = None
    downloader.xfer_type = ""
    downloader.xfer_comment = None

    downloader.update()

    assert not resumed_pages
    assert completed_runs == [41]
    assert downloader.xfer_status == "success"
    assert import_updates[0]["values"]["xfer_start_ts"] == datetime.datetime(2026, 8, 26, 12, 0, 0)


def test_cursor_download_advances_only_after_storing_a_page(caplog):
    caplog.set_level(logging.INFO, logger="gn2pg.download")
    requested_params = []
    stored_ids = []
    storage_keys = []
    saved_cursors = []
    responses = iter(
        [
            {"items": [{"observation_id": 1}, {"observation_id": 2}], "total_filtered": 3},
            {"items": [{"observation_id": 5}], "total_filtered": 3},
        ]
    )
    downloader = object.__new__(DownloadGn)
    downloader._config = SimpleNamespace(
        pagination_strategy="cursor",
        id_key_name="observation_id",
        uuid_key_name="observation_uuid",
        cursor_start=0,
        max_page_length=2,
        name="Source",
    )
    downloader._api_instance = SimpleNamespace(
        controler="data",
        get_cursor_page=lambda params: requested_params.append(dict(params)) or next(responses),
    )
    downloader._backend = SimpleNamespace(
        import_log=lambda **kwargs: None,
        store_data=lambda controler, items, **kwargs: (
            storage_keys.append((kwargs["id_key_name"], kwargs["uuid_key_name"]))
            or stored_ids.extend(item["observation_id"] for item in items)
            or len(items),
            len(stored_ids),
            0,
            0,
            0,
        ),
        save_cursor=lambda column, value: saved_cursors.append(value),
        complete_cursor=lambda: None,
    )
    downloader.api_count_items = 0
    downloader.data_count_upserts = 0
    downloader.data_count_errors = 0
    downloader.metadata_count_upserts = 0
    downloader.metadata_count_errors = 0
    downloader.xfer_comment = None

    assert downloader._execute_cursor_transfer({"limit": 2}, "full")

    assert stored_ids == [1, 2, 5]
    assert storage_keys == [
        ("observation_id", "observation_uuid"),
        ("observation_id", "observation_uuid"),
    ]
    assert saved_cursors == [2, 5]
    assert requested_params[0]["filter_n_up_observation_id"] == 0
    assert requested_params[1]["filter_n_up_observation_id"] == 3
    assert requested_params[0]["orderby"] == "observation_id:ASC"
    assert "Stores 2 datas (2/3 66.67 %)" in caplog.text
    assert "Stores 1 datas (3/3 100.00 %)" in caplog.text


def test_full_cursor_resume_starts_after_last_committed_identifier():
    requested_params = []
    saved_cursors = []
    downloader = object.__new__(DownloadGn)
    downloader._config = SimpleNamespace(
        data_type="synthese",
        pagination_strategy="cursor",
        id_key_name="id_synthese",
        uuid_key_name="id_perm_sinp",
        cursor_start=0,
        max_page_length=100,
        name="Source",
    )
    downloader._api_instance = SimpleNamespace(
        controler="data",
        get_cursor_page=lambda params: requested_params.append(dict(params))
        or {"items": [{"id_synthese": 43}], "total_filtered": 1},
    )
    downloader._backend = SimpleNamespace(
        resumable_cursor=lambda controler, xfer_type: {
            "id": 40,
            "xfer_start_ts": datetime.datetime(2026, 8, 25, 8, 0, 0),
            "xfer_filters": {"limit": 100, "filter_d_lo_derniere_action": "2026-08-25"},
            "cursor_value": 42,
        },
        import_log=lambda **kwargs: None,
        supersede_cursor=lambda import_id: None,
        store_data=lambda controler, items, **kwargs: (len(items), len(items), 0, 0, 0),
        save_cursor=lambda column, value: saved_cursors.append(value),
        complete_cursor=lambda: None,
    )
    downloader.api_count_items = 0
    downloader.data_count_upserts = 0
    downloader.data_count_errors = 0
    downloader.metadata_count_upserts = 0
    downloader.metadata_count_errors = 0
    downloader.xfer_comment = None

    downloader.store()

    assert requested_params[0]["filter_n_up_id_synthese"] == 43
    assert saved_cursors == [43]
    assert downloader.xfer_status == "success"


def test_retry_failed_resumes_cursor_without_starting_a_new_window():
    requested_params = []
    downloader = object.__new__(DownloadGn)
    downloader._config = SimpleNamespace(
        pagination_strategy="cursor",
        id_key_name="id_synthese",
        uuid_key_name="id_perm_sinp",
        cursor_start=0,
        max_page_length=100,
        name="Source",
    )
    downloader._api_instance = SimpleNamespace(
        controler="data",
        get_cursor_page=lambda params: requested_params.append(dict(params))
        or {"items": [{"id_synthese": 43}], "total_filtered": 1},
    )
    downloader._backend = SimpleNamespace(
        resumable_cursor=lambda controler, xfer_type: {
            "id": 40,
            "xfer_type": "full",
            "xfer_start_ts": datetime.datetime(2026, 8, 25, 8, 0, 0),
            "xfer_filters": {"limit": 100, "filter_d_lo_derniere_action": "2026-08-25"},
            "cursor_column": "id_synthese",
            "cursor_value": 42,
        },
        import_log=lambda **kwargs: None,
        supersede_cursor=lambda import_id: None,
        store_data=lambda controler, items, **kwargs: (len(items), len(items), 0, 0, 0),
        save_cursor=lambda column, value: None,
        complete_cursor=lambda: None,
    )
    downloader.resume_delete = lambda: False
    downloader.api_count_items = 0
    downloader.data_count_upserts = 0
    downloader.data_count_errors = 0
    downloader.metadata_count_upserts = 0
    downloader.metadata_count_errors = 0
    downloader.xfer_comment = None

    assert downloader.retry_failed()

    assert requested_params[0]["filter_n_up_id_synthese"] == 43
    assert requested_params[0]["filter_d_lo_derniere_action"] == "2026-08-25"
    assert downloader.xfer_status == "success"


def test_new_cursor_update_does_not_filter_old_identifiers_on_first_page():
    requested_params = []
    responses = iter(
        [
            {
                "items": [{"id_synthese": 1}, {"id_synthese": 2}],
                "total_filtered": 3,
            },
            {"items": [{"id_synthese": 5}], "total_filtered": 1},
        ]
    )
    downloader = object.__new__(DownloadGn)
    downloader._config = SimpleNamespace(
        pagination_strategy="cursor",
        id_key_name="id_synthese",
        uuid_key_name="id_perm_sinp",
        cursor_start=1000,
        max_page_length=2,
        name="Source",
    )
    downloader._api_instance = SimpleNamespace(
        controler="data",
        get_cursor_page=lambda params: requested_params.append(dict(params)) or next(responses),
    )
    downloader._backend = SimpleNamespace(
        import_log=lambda **kwargs: None,
        store_data=lambda controler, items, **kwargs: (len(items), len(items), 0, 0, 0),
        save_cursor=lambda column, value: None,
        complete_cursor=lambda: None,
    )
    downloader.api_count_items = 0
    downloader.data_count_upserts = 0
    downloader.data_count_errors = 0
    downloader.metadata_count_upserts = 0
    downloader.metadata_count_errors = 0
    downloader.xfer_comment = None

    assert downloader._execute_cursor_transfer(
        {
            "limit": 2,
            "filter_d_up_derniere_action": "2026-08-26 00:00:00",
            "filter_d_lo_derniere_action": "2026-08-27 00:00:00",
            "filter_n_up_id_synthese": 1000,
        },
        "update",
    )

    assert "filter_n_up_id_synthese" not in requested_params[0]
    assert requested_params[1]["filter_n_up_id_synthese"] == 3

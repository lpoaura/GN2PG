from copy import deepcopy
from types import MethodType, SimpleNamespace
from unittest.mock import MagicMock

from sqlalchemy import Column, Integer, MetaData, PrimaryKeyConstraint, String, Table
from sqlalchemy.exc import StatementError

from gn2pg.download import DownloadGn
from gn2pg.store_postgresql import StorePostgresql
from gn2pg.utils import XferStatus


def _transactional_backend():
    backend = object.__new__(StorePostgresql)
    backend._config = SimpleNamespace(data_type="synthese", std_name="source")
    backend.import_id = 1
    backend.count_data_upserts = 0
    backend.count_data_errors = 0
    backend.count_metadata_inserts = 0
    backend.count_metadata_errors = 0

    metadata = MetaData()
    data_table = Table(
        "data_json",
        metadata,
        Column("id_data", Integer),
        Column("controler", String),
        Column("type", String),
        Column("uuid", String),
        Column("source", String),
        Column("item", String),
        Column("update_ts", String),
        Column("import_id", Integer),
        PrimaryKeyConstraint("id_data", "controler", "source", name="pk_source_data"),
    )
    backend._table_defs = {"data": {"metadata": data_table}}
    backend._db = MagicMock()
    return backend


def test_store_data_commits_with_transaction_context():
    backend = _transactional_backend()
    conn = backend._db.begin.return_value.__enter__.return_value
    conn.execute.return_value.rowcount = 1

    backend.store_1_data("data", {"id_synthese": 42, "id_perm_sinp": "uuid"})

    backend._db.begin.assert_called_once_with()
    backend._db.begin.return_value.__exit__.assert_called_once_with(None, None, None)
    assert backend.count_data_upserts == 1


def test_store_data_updates_only_when_identity_and_uuid_match():
    backend = _transactional_backend()
    conn = backend._db.begin.return_value.__enter__.return_value
    insert_result = MagicMock(rowcount=0)
    update_result = MagicMock(rowcount=1)
    conn.execute.side_effect = [insert_result, update_result]

    backend.store_1_data("data", {"id_synthese": 42, "id_perm_sinp": "uuid"})

    assert conn.execute.call_count == 2
    insert_stmt = conn.execute.call_args_list[0].args[0]
    assert "ON CONFLICT DO NOTHING" in str(insert_stmt)
    update_stmt = conn.execute.call_args_list[1].args[0]
    compiled = str(update_stmt)
    assert "data_json.id_data = :id_data_1" in compiled
    assert "data_json.controler = :controler_1" in compiled
    assert "data_json.source = :source_1" in compiled
    assert "data_json.uuid = :uuid_1" in compiled
    assert backend.count_data_upserts == 1


def test_store_data_keeps_existing_row_on_uuid_or_identity_conflict(caplog):
    backend = _transactional_backend()
    conn = backend._db.begin.return_value.__enter__.return_value
    conn.execute.side_effect = [MagicMock(rowcount=0), MagicMock(rowcount=0)]

    backend.store_1_data("data", {"id_synthese": 42, "id_perm_sinp": "uuid"})

    assert backend.count_data_upserts == 0
    assert backend.count_data_errors == 0
    assert "was ignored" in caplog.text


def test_store_data_rolls_back_before_logging_error():
    backend = _transactional_backend()
    statement_error = StatementError("invalid data", None, None, ValueError("invalid"))
    backend._db.begin.return_value.__enter__.return_value.execute.side_effect = statement_error
    backend.error_log = MagicMock()

    backend.store_1_data("data", {"id_synthese": 42, "id_perm_sinp": "uuid"})

    exit_call = backend._db.begin.return_value.__exit__.call_args.args
    assert exit_call[0] is StatementError
    backend.error_log.assert_called_once()
    assert backend.count_data_upserts == 0
    assert backend.count_data_errors == 1


def test_metadata_export_items_are_split_into_framework_and_datasets():
    backend = object.__new__(StorePostgresql)
    backend._config = SimpleNamespace(std_name="source")
    backend.count_metadata_inserts = 0
    backend.count_metadata_errors = 0
    stored = []

    def fake_store(self, controler, level, elem, uuid_key_name="uuid"):
        stored.append((controler, level, elem))
        self.count_metadata_inserts += 1

    backend.store_1_metadata = MethodType(fake_store, backend)
    items = [
        {
            "id_acquisition_framework": 1184,
            "jsonb_insert": {
                "uuid": "c82201dc-4925-4749-bdbf-005a918c50b3",
                "name": "Framework",
                "datasets": [
                    {
                        "uuid": "9becc815-6b28-42e2-92ff-d11e95f2f1d2",
                        "name": "Dataset",
                    }
                ],
            },
        }
    ]
    original_items = deepcopy(items)

    result = backend.store_metadata(items)

    assert result == (1, 2, 0)
    assert stored[0][0:2] == ("metadata", "acquisition framework")
    assert "datasets" not in stored[0][2]
    assert stored[1][0:2] == ("metadata", "dataset")
    assert stored[1][2]["ca_uuid"] == "c82201dc-4925-4749-bdbf-005a918c50b3"
    assert items == original_items


def _downloader(data_type):
    downloader = object.__new__(DownloadGn)
    downloader._config = SimpleNamespace(
        data_type=data_type,
        max_page_length=100,
        query_strings={},
        nb_threads=1,
        name="Source",
    )
    downloader.xfer_status = XferStatus.init
    downloader.metadata_count_upserts = 0
    downloader.metadata_count_errors = 0
    downloader.api_count_items = 0
    return downloader


def test_metadata_only_full_download_does_not_download_data():
    downloader = _downloader("metadata_only")
    calls = []
    downloader.store_metadata = lambda xfer_type: calls.append(("metadata", xfer_type)) or True
    downloader._api_instance = SimpleNamespace(page_list=lambda **kwargs: calls.append(("data",)))

    downloader.store()

    assert calls == [("metadata", "full")]
    assert downloader.xfer_status == XferStatus.success


def test_separated_full_download_starts_with_metadata():
    downloader = _downloader("synthese_with_metadata_separated")
    calls = []
    downloader.store_metadata = lambda xfer_type: calls.append(("metadata", xfer_type)) or True
    downloader._api_instance = SimpleNamespace(
        controler="data",
        page_list=lambda **kwargs: (calls.append((kwargs["kind"], "full")) or (None, 0, 200)),
    )

    downloader.store()

    assert calls == [("metadata", "full"), ("data", "full")]

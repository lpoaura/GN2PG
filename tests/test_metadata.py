from copy import deepcopy
from types import MethodType, SimpleNamespace

from gn2pg.download import DownloadGn
from gn2pg.store_postgresql import StorePostgresql
from gn2pg.utils import XferStatus


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

from types import SimpleNamespace
from unittest.mock import Mock

from gn2pg import helpers


def test_update_passes_since_override_to_each_enabled_source(monkeypatch):
    enabled_source = SimpleNamespace(enable=True)
    disabled_source = SimpleNamespace(enable=False)
    config = SimpleNamespace(source_list={"enabled": enabled_source, "disabled": disabled_source})
    update_source = Mock()
    monkeypatch.setattr(helpers, "update_1source", update_source)

    helpers.update(config, since="2022-06-05")

    update_source.assert_called_once_with(helpers.Data, enabled_source, since="2022-06-05")


def test_update_source_passes_since_override_to_downloader(monkeypatch):
    store = Mock()
    store_context = Mock()
    store_context.__enter__ = Mock(return_value=store)
    store_context.__exit__ = Mock(return_value=False)
    monkeypatch.setattr(helpers, "StorePostgresql", Mock(return_value=store_context))

    downloader = Mock(name="downloader")
    downloader.name = "data"
    controller = Mock(return_value=downloader)
    source = SimpleNamespace(name="source", source="source")

    helpers.update_1source(controller, source, since="2022-06-05")

    downloader.update.assert_called_once_with(since="2022-06-05")

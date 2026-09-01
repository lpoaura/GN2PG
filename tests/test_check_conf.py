import logging
from pathlib import Path

import pytest
from schema import SchemaError
from toml import loads

import gn2pg.check_conf as check_conf
from gn2pg import __version__


class TestCheckConf:
    def test_gn2pg_conf(self, gn2pg_conf):
        assert gn2pg_conf

    def test_complete_example_configuration(self, monkeypatch):
        config_dir = Path(check_conf.__file__).parent / "data"
        config_file = config_dir / "gn2pgconfig.toml"
        expected = loads(config_file.read_text(encoding="utf-8"))
        monkeypatch.setattr(check_conf, "CONFDIR", config_dir)

        config = check_conf.Gn2PgConf(file=config_file.name)

        assert config.version == __version__
        assert len(config.source_list) == len(expected["source"])

        expected_db = expected["db"]
        expected_tuning = expected["tuning"]
        for index, (source_name, source) in enumerate(config.source_list.items()):
            expected_source = expected["source"][index]
            assert source.source == index
            assert source.name == expected_source["name"]
            assert source.std_name == source_name
            assert source.user_name == expected_source["user_name"]
            assert source.user_password == expected_source["user_password"]
            assert source.url == expected_source["url"]
            assert source.data_export_id == expected_source["data_export_id"]
            assert source.metadata_export_id == expected_source.get("metadata_export_id")
            assert source.data_type == expected_source["data_type"]
            assert source.id_application == expected_source.get("id_application", 3)
            assert source.enable == expected_source.get("enable", True)
            assert source.query_strings == expected_source.get("query_strings", {})

            assert source.database.host == expected_db["db_host"]
            assert source.database.port == expected_db["db_port"]
            assert source.database.user == expected_db["db_user"]
            assert source.database.password == expected_db["db_password"]
            assert source.database.name == expected_db["db_name"]
            assert source.database.schema_import == expected_db["db_schema_import"]
            assert source.database.querystring == expected_db.get("db_querystring", {})

            assert source.max_page_length == expected_tuning.get("max_page_length", 1000)
            assert source.max_retry == expected_tuning.get("max_retry", 5)
            assert source.max_requests == expected_tuning.get("max_requests", 0)
            assert source.retry_delay == expected_tuning.get("retry_delay", 5)
            assert source.http_timeout == (
                expected_tuning.get("http_connect_timeout", 10),
                expected_tuning.get("http_read_timeout", 120),
            )
            assert source.unavailable_delay == expected_tuning.get("unavailable_delay", 600)
            assert source.lru_maxsize == expected_tuning.get("lru_maxsize", 32)
            assert source.nb_threads == expected_tuning.get("nb_threads", 1)

            secure_config = config.secure_dict(source_name)
            assert secure_config["_source"].user_password == "***"
            assert secure_config["_db"].password == "***"

    def test_deprecated_export_id_alias(self, tmp_path, monkeypatch, toml_conf, caplog):
        config_file = tmp_path / "deprecated_export_id.toml"
        config_file.write_text(toml_conf.replace("data_export_id =", "export_id ="))
        monkeypatch.setattr(check_conf, "CONFDIR", tmp_path)

        with caplog.at_level(logging.WARNING):
            config = check_conf.Gn2PgConf(file=config_file.name)

        source = next(iter(config.source_list.values()))
        expected_id = int(toml_conf.split("data_export_id =", maxsplit=1)[1].splitlines()[0])
        assert source.data_export_id == expected_id
        assert any(
            "export_id" in record.getMessage() and "data_export_id" in record.getMessage()
            for record in caplog.records
        )

    def test_metadata_export_id_for_separated_metadata(self, tmp_path, monkeypatch, toml_conf):
        config_file = tmp_path / "metadata_export_id.toml"
        config_file.write_text(
            toml_conf.replace(
                'data_type = "synthese_with_metadata"',
                'data_type = "synthese_with_metadata_separated"\n' "    metadata_export_id = 2",
            )
        )
        monkeypatch.setattr(check_conf, "CONFDIR", tmp_path)

        config = check_conf.Gn2PgConf(file=config_file.name)

        source = next(iter(config.source_list.values()))
        assert source.metadata_export_id == 2

    def test_metadata_export_id_is_optional_for_other_data_types(self, gn2pg_conf):
        source = next(iter(gn2pg_conf.source_list.values()))
        assert source.metadata_export_id is None

    def test_metadata_export_id_is_required_for_separated_metadata(
        self, tmp_path, monkeypatch, toml_conf
    ):
        config_file = tmp_path / "missing_metadata_export_id.toml"
        config_file.write_text(
            toml_conf.replace(
                'data_type = "synthese_with_metadata"',
                'data_type = "synthese_with_metadata_separated"',
            )
        )
        monkeypatch.setattr(check_conf, "CONFDIR", tmp_path)

        with pytest.raises(SchemaError, match="metadata_export_id"):
            check_conf.Gn2PgConf(file=config_file.name)

    def test_metadata_only_does_not_require_data_export_id(self, tmp_path, monkeypatch, toml_conf):
        config_file = tmp_path / "metadata_only.toml"
        lines = [
            line
            for line in toml_conf.replace(
                'data_type = "synthese_with_metadata"',
                'data_type = "metadata_only"\n    metadata_export_id = 2',
            ).splitlines()
            if not line.strip().startswith("data_export_id =")
        ]
        config_file.write_text("\n".join(lines))
        monkeypatch.setattr(check_conf, "CONFDIR", tmp_path)

        source = next(iter(check_conf.Gn2PgConf(file=config_file.name).source_list.values()))

        assert source.data_type == "metadata_only"
        assert source.data_export_id is None
        assert source.metadata_export_id == 2

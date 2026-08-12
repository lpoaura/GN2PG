import gn2pg.check_conf as check_conf


class TestCheckConf:
    def test_gn2pg_conf(self, gn2pg_conf):
        assert gn2pg_conf

    def test_data_export_id_alias(self, tmp_path, monkeypatch, toml_conf):
        config_file = tmp_path / "data_export_id.toml"
        config_file.write_text(toml_conf.replace("export_id =", "data_export_id ="))
        monkeypatch.setattr(check_conf, "CONFDIR", tmp_path)

        config = check_conf.Gn2PgConf(file=config_file.name)

        source = next(iter(config.source_list.values()))
        assert source.export_id == int(
            toml_conf.split("export_id =", maxsplit=1)[1].splitlines()[0]
        )

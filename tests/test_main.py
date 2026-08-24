# -*- coding: utf-8 -*-
# The parametrize function is generated, so this doesn't work:
#
#     from pytest.mark import parametrize
#
import pytest
from pytest import raises

from gn2pg import __project__, __version__
from gn2pg.main import arguments, main

parametrize = pytest.mark.parametrize


class TestMain(object):
    @parametrize("helparg", ["-h", "--help"])
    def test_help(self, helparg, capsys):
        with raises(SystemExit) as exc_info:
            main([helparg])
        out, err = capsys.readouterr()
        # Should have printed some sort of usage message. We don't
        # need to explicitly test the content of the message.
        assert "usage" in out
        # Should have used the program name from the argument
        # vector.
        assert "GeoNature 2 PostgreSQL Client application" in out
        # Should exit with zero return code.
        assert exc_info.value.code == 0


def test_database_migration_options_keep_flag_based_interface():
    """Database migration actions remain mutually exclusive CLI flags."""
    assert arguments(["db", "--upgrade", "config.toml"]).upgrade
    assert arguments(["db", "--stamp-existing", "config.toml"]).stamp_existing
    assert arguments(["db", "--status", "config.toml"]).status

    with raises(SystemExit):
        arguments(["db", "--upgrade", "--status", "config.toml"])


@parametrize("versionarg", ["-V", "--version"])
def test_version(versionarg, capsys):
    """The global version flags print project identification."""
    with raises(SystemExit) as exc_info:
        main([versionarg])
    out, _err = capsys.readouterr()
    assert all(elm in out for elm in [__project__, __version__])
    assert exc_info.value.code == 0

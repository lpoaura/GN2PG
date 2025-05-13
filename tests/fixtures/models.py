import pytest

from gn2pg.app.database import db
from gn2pg.app.models import ImportLog


@pytest.fixture
def import_log():
    source = ("source_demo_test_ns", "source_ecrins_light")
    controler = ("data", "data")
    donwload_ts = ("2023-03-14 12:00:00.000", "2023-03-14 11:51:16.926")
    error_count = (0, 1)
    http_status = (0, 0)
    importlog_list = []

    for src, ctrl, dwld_ts, err_cnt, http_st in zip(
        source, controler, donwload_ts, error_count, http_status
    ):
        importlog_list.append(
            ImportLog(
                source=src,
                controler=ctrl,
                download_ts=dwld_ts,
                error_count=err_cnt,
                http_status=http_st,
            )
        )
    with db.session.begin_nested():
        db.session.add_all(importlog_list)
    return importlog_list

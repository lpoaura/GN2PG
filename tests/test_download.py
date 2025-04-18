"""Test download"""

import datetime


class TestDownload:
    """Test download"""

    def test_store(self, data, caplog):
        """Test store"""
        data.store()
        now = datetime.datetime.now()
        increment = data._backend.increment_get(data._api_instance.controler)

        assert now.strftime("%d/%m/%Y %H") == increment.strftime("%d/%m/%Y %H")
        assert "items have been stored in db from" in caplog.text
        assert "100.00 %" in caplog.text

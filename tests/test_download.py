import datetime

class TestDownload:
    def test_store(self, data, caplog):
        data.store()
        now = datetime.datetime.now()
        increment = data._backend.increment_get(data._api_instance.controler)

        assert now.strftime("%d/%m/%Y %H") == increment.strftime("%d/%m/%Y %H")
        assert "items have been stored in db from data of source" in caplog.records[-1].message
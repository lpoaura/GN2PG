
import os
from gn2pg.app.config import Config



class TestConfig:
    def test_config_load_env(self):
        
        config =  Config

        assert os.environ.get('DB_USER') == config.DB_USER
        assert os.environ.get('DB_NAME') == config.DB_NAME
        assert os.environ.get('DB_PORT') == str(config.DB_PORT)
        assert os.environ.get('DB_HOST') == config.DB_HOST
        assert os.environ.get('ENV') == config.ENV
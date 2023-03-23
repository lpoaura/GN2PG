from pathlib import Path

from gn2pg import _

# DIRECTORY FOR SETTINGS.INI
BASE_DIR = Path(__file__).absolute().parent.parent.parent
SETTINGS_FILE = BASE_DIR.joinpath("install/settings.ini")

"""Module providing constant environment variable path directory."""

from pathlib import Path

# DIRECTORY FOR SETTINGS.INI
BASE_DIR = Path(__file__).absolute().parent.parent.parent
SETTINGS_FILE = BASE_DIR.joinpath("install/settings.ini")

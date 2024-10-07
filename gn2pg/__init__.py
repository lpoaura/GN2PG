# -*- coding: utf-8 -*-
"""Outil d'import de données entre instances GeoNature (côté client)"""

import gettext
import logging
import logging.config
from pathlib import Path

import coloredlogs

from importlib.metadata import version

from gn2pg import metadata

try:
    DIST_NAME = "gn2pg_client"
    __version__ = version(DIST_NAME)
except :  # pragma: no cover
    __version__ = metadata.VERSION
finally:
    del version

__author__ = metadata.AUTHORS_STRING
__license__ = metadata.LICENSE

coloredlogs.DEFAULT_FIELD_STYLES["module"] = {"color": "blue"}

logger = logging.getLogger(__name__)

coloredlogs.install(
    level="DEBUG",
    logger=logger,
    milliseconds=True,
    fmt="%(asctime)s - %(levelname)s - %(module)s:%(funcName)s - %(message)s",
)


# Install gettext for any file in the application
localedir = Path(__file__).resolve().parent / "locale"
gettext.bindtextdomain("gn2pg", str(localedir))
gettext.textdomain("gn2pg")
_ = gettext.gettext

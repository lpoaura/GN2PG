# -*- coding: utf-8 -*-
"""Outil d'import de données entre instances GeoNature (côté client)"""

import gettext
import logging
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from gn2pg import metadata

try:
    DIST_NAME = "gn2pg_client"
    __version__ = version(DIST_NAME)
except PackageNotFoundError:
    __version__ = metadata.VERSION
finally:
    del version

__author__ = metadata.AUTHORS_STRING
__license__ = metadata.LICENSE

logger = logging.getLogger(__name__)


# Install gettext for any file in the application
localedir = Path(__file__).resolve().parent / "locale"
gettext.bindtextdomain("gn2pg", str(localedir))
gettext.textdomain("gn2pg")
_ = gettext.gettext

# -*- coding: utf-8 -*-
"""Outil d'import de données entre instances GeoNature (côté client)"""

import gettext
import importlib.metadata
import logging
from pathlib import Path

from gn2pg import metadata

try:
    __version__ = importlib.metadata.version("gn2pg_client")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"


__author__ = metadata.AUTHORS_STRING
__license__ = metadata.LICENSE

logger = logging.getLogger(__name__)


# Install gettext for any file in the application
localedir = Path(__file__).resolve().parent / "locale"
gettext.bindtextdomain("gn2pg", str(localedir))
gettext.textdomain("gn2pg")
_ = gettext.gettext

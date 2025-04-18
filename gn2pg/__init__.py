# -*- coding: utf-8 -*-
"""Outil d'import de données entre instances GeoNature (côté client)"""

import gettext
import importlib.metadata
import logging
from pathlib import Path

pkg_metadata = importlib.metadata.metadata("GN2PG_client")

try:
    __version__ = importlib.metadata.version("GN2PG_client")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"

__project__ = "GeoNature 2 PostgreSQL Client application"
__author__ = pkg_metadata.get("Author")
__license__ = pkg_metadata.get("License")

logger = logging.getLogger(__name__)


# Install gettext for any file in the application
localedir = Path(__file__).resolve().parent / "locale"
gettext.bindtextdomain("gn2pg", str(localedir))
gettext.textdomain("gn2pg")
_ = gettext.gettext

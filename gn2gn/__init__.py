# -*- coding: utf-8 -*-
"""Outil d'import de données entre instances GeoNature (côté client)"""

from gn2gn_client import metadata
import logging
import logging.config
from .log_conf import my_logging_dict
import coloredlogs

__version__ = metadata.version
__author__ = metadata.authors[0]
__license__ = metadata.license
__copyright__ = metadata.copyright


logging.config.dictConfig(my_logging_dict)
logger = logging.getLogger("transfer_gn")
__version__ = metadata.version

coloredlogs.install(
    level="DEBUG",
    logger=logger,
    milliseconds=True,
    fmt="%(asctime)s - %(levelname)s - %(module)s:%(funcName)s - %(message)s",
)

# -*- coding: utf-8 -*-
"""Outil d'import de données entre instances GeoNature (côté client)"""

import gettext
import logging
import logging.config
from pathlib import Path

import coloredlogs
from pkg_resources import DistributionNotFound, get_distribution

from . import metadata

try:
    dist_name = "gn2gn_client"
    __version__ = get_distribution(dist_name).version
except DistributionNotFound:  # pragma: no cover
    __version__ = metadata.version
finally:
    del get_distribution, DistributionNotFound

__author__ = metadata.authors[0]
__license__ = metadata.license
__copyright__ = metadata.copyright

coloredlogs.DEFAULT_FIELD_STYLES["module"] = {"color": "blue"}

# my_logging_dict = {
#     "version": 1,
#     "disable_existing_loggers": True,  # set True to suppress existing loggers from other modules
#     "loggers": {
#         "root": {
#             "level": "DEBUG",
#             "handlers": ["console", "file"],
#         },
#     },
#     "formatters": {
#         "colored_console": {
#             "()": "coloredlogs.ColoredFormatter",
#             "format": "%(asctime)s - %(levelname)s - %(module)s:%(funcName)s - %(message)s",
#             "datefmt": "%H:%M:%S",
#         },
#         "format_for_file": {
#             "format": "%(asctime)s - %(levelname)s - %(module)s:%(funcName)s - %(message)s",
#             "datefmt": "%Y-%m-%d %H:%M:%S",
#         },
#     },
#     "handlers": {
#         "console": {
#             "level": "INFO",
#             "class": "logging.StreamHandler",
#             "formatter": "colored_console",
#             "stream": "ext://sys.stdout",
#         },
#         "file": {
#             "level": "INFO",
#             "class": "logging.handlers.TimedRotatingFileHandler",
#             "formatter": "format_for_file",
#             "filename": str(LOGDIR) + "/" + __name__ + ".log",
#             "maxBytes": 500000,
#             "backupCount": 5,
#         },
#     },
# }

# LOGDIR.mkdir(parents=True, exist_ok=True)

# logging.config.dictConfig(my_logging_dict)
logger = logging.getLogger("transfer_gn")

coloredlogs.install(
    level="DEBUG",
    logger=logger,
    milliseconds=True,
    fmt="%(asctime)s - %(levelname)s - %(module)s:%(funcName)s - %(message)s",
)


# Install gettext for any file in the application
localedir = Path(__file__).resolve().parent / "locale"
gettext.bindtextdomain("gn2gn", str(localedir))
gettext.textdomain("gn2gn")
_ = gettext.gettext

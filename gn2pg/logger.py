"""app logging config"""

import logging
from logging.handlers import TimedRotatingFileHandler

from gn2pg.env import LOGDIR

LOGDIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Set the custom logger class

logger = logging.getLogger("gn2pg")

filehandler = TimedRotatingFileHandler(
    str(LOGDIR / ("gn2pg" + ".log")),
    when="midnight",
    interval=1,
    backupCount=100,
)
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(module)s:%(funcName)s - %(message)s"
)
filehandler.setFormatter(formatter)

logger.addHandler(filehandler)

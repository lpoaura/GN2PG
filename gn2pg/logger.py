"""Logging config"""

import logging
from logging.handlers import TimedRotatingFileHandler

from .env import LOGDIR

logger = logging.getLogger(__name__)


def setup_logging(loglevel=logging.INFO):
    """Setup logging"""

    LOGDIR.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=loglevel,
        format="%(asctime)s - %(levelname)s - %(module)s:%(funcName)s - %(message)s",
        handlers=[
            logging.StreamHandler(),  # For stdout
            TimedRotatingFileHandler(
                str(LOGDIR / ("gn2pg" + ".log")), when="midnight", interval=1, backupCount=100
            ),
        ],
    )

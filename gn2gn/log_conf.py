from pathlib import Path
import coloredlogs

coloredlogs.DEFAULT_FIELD_STYLES["module"] = {"color": "blue"}

my_logging_dict = {
    "version": 1,
    "disable_existing_loggers": True,  # set True to suppress existing loggers from other modules
    "loggers": {
        "root": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
        },
    },
    "formatters": {
        "colored_console": {
            "()": "coloredlogs.ColoredFormatter",
            "format": "%(asctime)s - %(levelname)s - %(module)s:%(funcName)s - %(message)s",
            "datefmt": "%H:%M:%S",
        },
        "format_for_file": {
            "format": "%(asctime)s - %(levelname)s - %(module)s:%(funcName)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "colored_console",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "format_for_file",
            "filename": str(Path.home()) + "/tmp/" + __name__ + ".log",
            "maxBytes": 500000,
            "backupCount": 5,
        },
    },
}

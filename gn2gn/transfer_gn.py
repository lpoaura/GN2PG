#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Program entry point"""
import argparse
import logging
import logging.config
import shutil
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

import pkg_resources
import toml
from toml import TomlDecodeError

from . import metadata

from .log_conf import coloredlogs, my_logging_dict
from .check_conf import Gn2GnConf
from .utils import BColors
from .store_postgresql import PostgresqlUtils

# logging.config.dictConfig(my_logging_dict)
logger = logging.getLogger(__name__)
__version__ = metadata.version

# coloredlogs.install(
#     level="DEBUG",
#     logger=logger,
#     milliseconds=True,
#     fmt="%(asctime)s - %(levelname)s - %(module)s:%(funcName)s - %(message)s",
# )


def arguments(args):
    """Define and parse command arguments.

    Args:
        args ([str]): command line parameters as list of strings

    Returns:
        :obj:`argparse.Namespace`: command line parameters namespace
    """
    # Get options
    parser = argparse.ArgumentParser(description="Gn2Gn Client app")
    parser.add_argument(
        "--version",
        help="Print version number",
        action="version",
        version="%(prog)s {version}".format(version=__version__),
    )
    out_group = parser.add_mutually_exclusive_group()
    out_group.add_argument(
        "--verbose", help="Increase output verbosity", action="store_true"
    )
    out_group.add_argument(
        "--quiet", help="Reduce output verbosity", action="store_true"
    )
    parser.add_argument(
        "--init", help="Initialize the TOML configuration file", action="store_true"
    )
    parser.add_argument(
        "--json-tables-create",
        help="Create or recreate json tables",
        action="store_true",
    )
    parser.add_argument("file", help="Configuration file name")

    return parser.parse_args(args)


def main(args):
    """Main entry point allowing external calls

    Args:
      args ([str]): command line parameter list
    """
    logger = logging.getLogger("transfer_gn")
    author_strings = []
    for name, email in zip(metadata.authors, metadata.emails):
        author_strings.append("Author: {0} <{1}>".format(name, email))

    epilog = """
{project} {version}

{authors}
URL: <{url}>
""".format(
        project=metadata.project,
        version=__version__,
        authors="\n".join(author_strings),
        url=metadata.url,
    )

    print(epilog)

    # Create $HOME/tmp directory if it does not exist
    (Path.home() / "tmp").mkdir(exist_ok=True)

    # create file handler which logs even debug messages
    fh = TimedRotatingFileHandler(
        str(Path.home()) + "/tmp/" + __name__ + ".log",
        when="midnight",
        interval=1,
        backupCount=100,
    )
    # create console handler with a higher log level
    # ch = logging.StreamHandler()
    # create formatter and add it to the handlers
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(module)s:%(funcName)s - %(message)s"
    )
    fh.setFormatter(formatter)
    # ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    # logger.addHandler(ch)

    # Get command line arguments
    args = arguments(args)
    # Define verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    elif args.quiet:
        logger.setLevel(logging.WARNING)
    else:
        logger.setLevel(logging.INFO)

    logger.info("%s, version %s", sys.argv[0], __version__)
    logger.debug("Args: %s", args)
    logger.info("Arguments: %s", sys.argv[1:])

    # If required, first create YAML file
    if args.init:
        logger.info("Creating TOML configuration file")
        init(args.file)
        return None

    # Get configuration from file
    if not (Path.home() / args.file).is_file():
        logger.critical(
            "Configuration file %s does not exist", str(Path.home() / args.file)
        )
        return None
    logger.info("Getting configuration data from %s", args.file)
    try:
        cfg_ctrl = Gn2GnConf(args.file)
    except TomlDecodeError:
        logger.critical(
            f"Incorrect content in TOML configuration {args.file}",
        )
        sys.exit(0)
    # try:
    #     config_schema.validate(cfg_ctrl)
    #     logger.info(f"Config file is valid")
    # except Exception as e:
    #     logger.critical(f"Config file is not valid:\n{e}")
    #     return None
    cfg_source_list = cfg_ctrl.source_list
    cfg = list(cfg_source_list.values())[0]
    cfg_source_list
    logger.info(
        f"config file have {len(cfg_source_list)} source(s) wich are : {', '.join([src for src in cfg_source_list.keys()])}"
    )

    manage_pg = PostgresqlUtils(cfg)

    if args.json_tables_create:
        logger.info("Create, if not exists, json tables")
        manage_pg.create_json_tables()

    return None


def init(file: str):
    """

    Args:
        config:

    Returns:

    """
    logger = logging.getLogger("transfer_gn")
    toml_src = pkg_resources.resource_filename(__name__, "data/gn2gnconfig.toml")
    toml_dst = str(Path.home() / file)
    if Path(toml_dst).is_file():
        logger.warning(f"{toml_dst} file already exists")
        overwrite = input(
            f"{BColors.HEADER}Would you like to overwrite file {toml_dst}{BColors.ENDC} ([{BColors.BOLD}y{BColors.ENDC}]es/[{BColors.BOLD}n{BColors.ENDC}]o) ? "
        )
        if overwrite.lower() == "n":
            logger.warning(f"File {toml_dst} will be preserved")
            exit()
        else:
            logger.warning(f"file {toml_dst} will be overwritten")
    logger.info(f"Creating TOML configuration file {toml_dst}, from {toml_src}")
    shutil.copyfile(toml_src, toml_dst)
    logger.info(f"Please edit {toml_dst} before running the script")
    sys.exit(0)


def run():
    """Zero-argument entry point for use with setuptools/distribute."""
    # raise SystemExit(main(sys.argv))
    return main(sys.argv[1:])


if __name__ == "__main__":
    run()

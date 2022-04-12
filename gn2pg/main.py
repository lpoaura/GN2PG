#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Program entry point"""

import argparse
import logging
import logging.config
import sys
from logging.handlers import TimedRotatingFileHandler
from typing import NoReturn

from toml import TomlDecodeError

from . import _, __version__, metadata
from .check_conf import Gn2PgConf
from .env import ENVDIR, LOGDIR
from .helpers import edit, full_download, init, update
from .store_postgresql import PostgresqlUtils
from .utils import BColors

logger = logging.getLogger(__name__)


def arguments(args):
    """Define and parse command arguments.

    Args:
        args ([str]): command line parameters as list of strings

    Returns:
        :obj:`argparse.Namespace`: command line parameters namespace
    """
    # Get options
    parser = argparse.ArgumentParser(description="Gn2Pg Client app")
    parser.add_argument(
        "-V",
        "--version",
        help=_("Print version number"),
        action="version",
        version="%(prog)s {version}".format(version=__version__),
    )
    out_group = parser.add_mutually_exclusive_group()
    out_group.add_argument(
        "-v",
        "--verbose",
        help=_("Increase output verbosity"),
        action="store_true",
    )
    out_group.add_argument(
        "-q", "--quiet", help=_("Reduce output verbosity"), action="store_true"
    )
    parser.add_argument(
        "--init",
        help=_("Initialize the TOML configuration file"),
        action="store_true",
    )
    parser.add_argument(
        "--edit",
        help=_("Edit the TOML configuration file in default editor"),
        action="store_true",
    )
    parser.add_argument(
        "--json-tables-create",
        help=_("Create or recreate json tables"),
        action="store_true",
    )
    customscript_group = parser.add_mutually_exclusive_group()
    customscript_group.add_argument(
        "--custom-script",
        nargs="?",
        help=_(
            '''Execute custom SQL script in DB, default is "to_gnsynthese".
        You can also use your own script by using absolute file path instead of "to_gnsynthese"'''
        ),
    )
    download_group = parser.add_mutually_exclusive_group()
    download_group.add_argument(
        "--full", help=_("Perform a full download"), action="store_true"
    )
    download_group.add_argument(
        "--update",
        help=_("Perform an incremental download"),
        action="store_true",
    )
    parser.add_argument("file", help="Configuration file name")

    return parser.parse_args(args)


def main(args) -> NoReturn:
    """Main entry point allowing external calls

    Args:
      args ([str]): command line parameter list
    """
    logger = logging.getLogger("transfer_gn")

    epilog = f"""{BColors.OKBLUE}{BColors.BOLD}{metadata.project}{BColors.ENDC}{BColors.ENDC} \
{BColors.BOLD}{BColors.HEADER}{__version__}{BColors.ENDC}{BColors.ENDC}
{BColors.BOLD}LICENSE{BColors.ENDC}: {metadata.license}
{BColors.BOLD}AUTHORS{BColors.ENDC}: {metadata.authors_string}
{BColors.BOLD}COPYRIGHT{BColors.ENDC}: {metadata.copyright}

{BColors.BOLD}URL{BColors.ENDC}: {metadata.url}
{BColors.BOLD}DOCS{BColors.ENDC}: {metadata.docs}
"""
    print(epilog)

    # Create $HOME/tmp directory if it does not exist
    LOGDIR.mkdir(parents=True, exist_ok=True)

    # create file handler which logs even debug messages
    fh = TimedRotatingFileHandler(
        str(LOGDIR / (__name__ + ".log")),
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

    # Edit yaml config file
    if args.edit:
        logger.info("Editing TOML configuration file")
        edit(args.file)
        return None

    # Get configuration from file
    if not (ENVDIR / args.file).is_file():
        logger.critical(
            "Configuration file %s does not exist", str(ENVDIR / args.file)
        )
        return None
    logger.info("Getting configuration data from %s", args.file)
    try:
        cfg_ctrl = Gn2PgConf(args.file)
    except TomlDecodeError:
        logger.critical(
            f"Incorrect content in TOML configuration {args.file}",
        )
        sys.exit(0)
    cfg_source_list = cfg_ctrl.source_list
    cfg = list(cfg_source_list.values())[0]
    logger.info(
        f"config file have {len(cfg_source_list)} source(s) wich are : "
        f"{', '.join([src for src in cfg_source_list.keys()])}"
    )

    manage_pg = PostgresqlUtils(cfg)

    if args.json_tables_create:
        logger.info("Create, if not exists, json tables")
        manage_pg.create_json_tables()

    if args.custom_script:
        logger.info(_(f"Execute custom script {args.custom_script} on db"))
        manage_pg.custom_script(args.custom_script)

    if args.full:
        logger.info("Perform full action")
        full_download(cfg_ctrl)

    if args.update:
        logger.info("Perform update action")
        update(cfg_ctrl)


def run():
    """Zero-argument entry point for use with setuptools/distribute."""
    # raise SystemExit(main(sys.argv))
    return main(sys.argv[1:])


if __name__ == "__main__":
    run()

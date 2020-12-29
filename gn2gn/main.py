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
from subprocess import call

import pkg_resources
from toml import TomlDecodeError

from . import _, __version__, metadata
from .check_conf import Gn2GnConf
from .download import Datasets, Synthese
from .env import ENVDIR, LOGDIR
from .store_postgresql import PostgresqlUtils, StorePostgresql
from .utils import BColors

logger = logging.getLogger(__name__)

CTRL_DEFS = {
    "synthese": Synthese,
    "dataset": Datasets,
}


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
        "-V",
        "--version",
        help=_("Print version number"),
        action="version",
        version="%(prog)s {version}".format(version=__version__),
    )
    out_group = parser.add_mutually_exclusive_group()
    out_group.add_argument(
        "-v", "--verbose", help=_("Increase output verbosity"), action="store_true",
    )
    out_group.add_argument(
        "-q", "--quiet", help=_("Reduce output verbosity"), action="store_true"
    )
    parser.add_argument(
        "--init", help=_("Initialize the TOML configuration file"), action="store_true",
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
    download_group = parser.add_mutually_exclusive_group()
    download_group.add_argument(
        "--full", help=_("Perform a full download"), action="store_true"
    )
    download_group.add_argument(
        "--update", help=_("Perform an incremental download"), action="store_true",
    )
    parser.add_argument("file", help="Configuration file name")

    return parser.parse_args(args)


def main(args):
    """Main entry point allowing external calls

    Args:
      args ([str]): command line parameter list
    """
    logger = logging.getLogger("transfer_gn")

    epilog = f"""{BColors.OKBLUE}{BColors.BOLD}{metadata.project}{BColors.ENDC}{BColors.ENDC} \
{BColors.BOLD}{BColors.HEADER}{__version__}{BColors.ENDC}{BColors.ENDC}
{BColors.BOLD}URL{BColors.ENDC}: <{metadata.url}>
"""
    print(epilog)

    # Create $HOME/tmp directory if it does not exist
    LOGDIR.mkdir(parents=True, exist_ok=True)

    # create file handler which logs even debug messages
    fh = TimedRotatingFileHandler(
        str(LOGDIR / (__name__ + ".log")), when="midnight", interval=1, backupCount=100,
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

    # If required, first create YAML file
    if args.edit:
        logger.info("Editing TOML configuration file")
        edit(args.file)
        return None

    # Get configuration from file
    if not (ENVDIR / args.file).is_file():
        logger.critical("Configuration file %s does not exist", str(ENVDIR / args.file))
        return None
    logger.info("Getting configuration data from %s", args.file)
    try:
        cfg_ctrl = Gn2GnConf(args.file)
    except TomlDecodeError:
        logger.critical(f"Incorrect content in TOML configuration {args.file}",)
        sys.exit(0)
    # try:
    #     config_schema.validate(cfg_ctrl)
    #     logger.info(f"Config file is valid")
    # except Exception as e:
    #     logger.critical(f"Config file is not valid:\n{e}")
    #     return None
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

    if args.full:
        logger.info("Perform full action")
        full_download(cfg_ctrl)

    return None


def init(file: str):
    """

    Args:
        config:

    Returns:

    """
    logger = logging.getLogger("transfer_gn")
    toml_src = pkg_resources.resource_filename(__name__, "data/gn2gnconfig.toml")
    toml_dst = str(ENVDIR / file)
    if Path(toml_dst).is_file():
        ENVDIR.mkdir(exist_ok=True)
        logger.info(f"Conf directory {str(ENVDIR)} created")
        logger.warning(f"{toml_dst} file already exists")
        overwrite = input(
            f"{BColors.HEADER}Would you like to overwrite file {toml_dst}{BColors.ENDC} "
            f"([{BColors.BOLD}y{BColors.ENDC}]es/[{BColors.BOLD}n{BColors.ENDC}]o) ? "
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


def edit(file: str):
    """Open editor to edit config file

    Args:
        file (str): [description]
    """
    config_file = ENVDIR / file
    call(["editor", config_file])


def full_download_1source(ctrl, cfg):
    """Downloads from a single controler."""
    logger = logging.getLogger("transfer_gn")
    # logger.debug(_(f"Enter full_download_1: {ctrl.__name__}"))
    logger.debug(cfg)
    with StorePostgresql(cfg) as store_pg:
        downloader = ctrl(cfg, store_pg)
        logger.debug(
            _(f"{cfg.source} => Starting download using controler {downloader.name}")
        )
        downloader.store()
        logger.info(
            _(f"{cfg.source} => Ending download using controler {downloader.name}")
        )


def full_download(cfg_ctrl):
    """Performs a full download of all sites and controlers,
    based on configuration file."""
    logger = logging.getLogger("transfer_gn")
    logger.info(cfg_ctrl)
    cfg_source_list = cfg_ctrl.source_list
    cfg = list(cfg_source_list.values())[0]
    logger.info(_("Defining full download jobs"))
    for source, cfg in cfg_source_list.items():
        if cfg.enable:
            logger.info(_(f"Starting full download for source {source}"))
            # full_download_1(Datasets, cfg)
            full_download_1source(Synthese, cfg)
        else:
            logger.info(_(f"Source {source} is disabled"))

    return None


def run():
    """Zero-argument entry point for use with setuptools/distribute."""
    # raise SystemExit(main(sys.argv))
    return main(sys.argv[1:])


if __name__ == "__main__":
    run()

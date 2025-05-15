#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Program entry point"""

import argparse
import logging

# import logging.config
import sys

import coloredlogs
from toml import TomlDecodeError

from gn2pg import _, __project__, __version__, pkg_metadata
from gn2pg.check_conf import Gn2PgConf
from gn2pg.env import CONFDIR
from gn2pg.helpers import full_download, init, manage_configs, update
from gn2pg.logger import setup_logging
from gn2pg.store_postgresql import PostgresqlUtils
from gn2pg.utils import BColors

logger = logging.getLogger(__name__)

sh_col = BColors()


def arguments(args):
    """Define and parse command arguments.

    Args:
        args ([str]): command line parameters as list of strings

    Returns:
        :obj:`argparse.Namespace`: command line parameters namespace
    """
    # Get options
    parser = argparse.ArgumentParser(description="Gn2Pg Client app")

    subparser = parser.add_subparsers(help=_("Config management commands"), required=True)

    config_parser = subparser.add_parser("config", help=_("Manage configs"))
    download_parser = subparser.add_parser("download", help=_("Manage downloads"))
    db_parser = subparser.add_parser("db", help=_("Manage downloads"))

    # Global commands
    parser.add_argument(
        "-V",
        "--version",
        help=_("Print version number"),
        action="version",
        version=f"%(prog)s v{__version__}",
    )
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "-v",
        "--verbose",
        help=_("Increase output verbosity"),
        action="store_true",
    )
    output_group.add_argument(
        "-q", "--quiet", help=_("Reduce output verbosity"), action="store_true"
    )

    # Config commands
    config_group = config_parser.add_mutually_exclusive_group(required=True)
    config_group.add_argument(
        "--init",
        nargs="?",
        type=str,
        const="config.toml",
        help=_("Initialize the TOML configuration file"),
    )
    config_group.add_argument(
        "--list",
        help=_("List config files"),
        action="store_true",
    )
    config_group.add_argument(
        "--read",
        nargs="?",
        type=str,
        default=None,
        const="empty",
        help=_("Select and view config file"),
    )
    config_group.add_argument(
        "--edit",
        nargs="?",
        type=str,
        default=None,
        const="empty",
        help=_("Select and view config file"),
    )

    # database commands
    db_group = db_parser.add_mutually_exclusive_group(required=True)
    db_group.add_argument(
        "--custom-script",
        nargs="?",
        type=str,
        help=_(
            '''Execute custom SQL script in DB, default is "to_gnsynthese".
        You can also use your own script by using absolute file path instead of "to_gnsynthese"'''
        ),
    )
    db_group.add_argument(
        "--json-tables-create",
        help=_("Create or recreate json tables"),
        action="store_true",
    )

    # Download commands
    download_group = download_parser.add_mutually_exclusive_group(required=True)

    download_group.add_argument("--full", help=_("Perform a full download"), action="store_true")
    download_group.add_argument(
        "--update",
        help=_("Perform an incremental download"),
        action="store_true",
    )

    for p in (db_parser, download_parser):
        p.add_argument("file", nargs="?", help="Configuration file name")

    return parser.parse_args(args)


def main(args) -> None:
    """Main entry point allowing external calls

    Args:
      args ([str]): command line parameter list
    """
    newline_char = "\n"
    epilog = f"""\
{sh_col.color('okblue')}{sh_col.color('bold')}{__project__} \
{sh_col.color('endc')}{sh_col.color('endc')} \
{sh_col.color('bold')}{sh_col.color('header')}{__version__} \
{sh_col.color('endc')}{sh_col.color('endc')}
{sh_col.color('bold')}LICENSE{sh_col.color('endc')}: {pkg_metadata.get('License')}
{sh_col.color('bold')}AUTHORS{sh_col.color('endc')}: {pkg_metadata.get('Author')}

{newline_char.join(pkg_metadata.get_all('Project-URL'))}
"""
    print(epilog)

    args = arguments(args)

    # Setup logging
    loglevel = logging.INFO
    if args.verbose:
        loglevel = logging.DEBUG
    if args.quiet:
        loglevel = logging.WARNING
    setup_logging(loglevel)
    coloredlogs.install(
        level=loglevel,
        logger=logger,
        milliseconds=True,
        fmt="%(asctime)s - %(levelname)s - %(module)s:%(funcName)s - %(message)s",
    )

    logger.info(_("%s, version %s"), sys.argv[0], __version__)
    logger.debug("Args: %s", args)
    logger.debug("Arguments: %s", sys.argv[1:])

    if "config" in sys.argv:
        handle_config_commands(args)

    if any(cmd in ["download", "db"] for cmd in sys.argv):
        if args.file is None:
            logger.critical(_("You must provide a config file"))
            sys.exit(0)
        try:
            cfg_ctrl = Gn2PgConf(args.file)
        except TomlDecodeError as e:
            logger.critical(_("Incorrect content in TOML configuration %s : %s"), args.file, e)
            sys.exit(0)

        if "db" in sys.argv:
            handle_database_commands(args, cfg_ctrl)
        if "download" in sys.argv:
            handle_download_commands(args, cfg_ctrl)


def handle_download_commands(args, cfg_ctrl) -> bool:
    """Handle commands that are not related to 'manage'."""

    if not (CONFDIR / args.file).is_file():
        logger.critical(_("Configuration file %s does not exist"), str(CONFDIR / args.file))
        return False

    logger.info(_("Getting configuration data from %s"), args.file)

    if args.full:
        logger.info(_("Perform full action"))
        full_download(cfg_ctrl)

    if args.update:
        logger.info(_("Perform update action"))
        update(cfg_ctrl)

    return True


def handle_database_commands(args, cfg_ctrl) -> None:
    """Handle commands related to 'config'."""

    cfg_source_list = cfg_ctrl.source_list
    cfg = list(cfg_source_list.values())[0]
    logger.info(
        _("config file have {len(cfg_source_list)} source(s) wich are : %s"),
        ", ".join(cfg_source_list.keys()),
    )

    manage_pg = PostgresqlUtils(cfg)

    if args.json_tables_create:
        logger.info(_("Create, if not exists, json tables"))
        manage_pg.create_json_tables()
    if args.custom_script:
        logger.info(_("Execute custom script %s on db"), args.custom_script)
        manage_pg.custom_script(args.custom_script)


def handle_config_commands(args) -> None:
    """Handle commands related to 'config'."""
    print(args)
    if args.init:
        logger.info(_(f"Creating TOML configuration file {args.init}"))
        init(args.init)
    if args.list:
        logger.info(_("List config files"))
        manage_configs("list")
    if args.read:
        logger.info(_("Read config"))
        manage_configs("read", args.read)
    if args.edit:
        logger.info(_("Edit config"))
        manage_configs("edit", args.edit)


def run():
    """Zero-argument entry point for use with setuptools/distribute."""
    # raise SystemExit(main(sys.argv))
    return main(sys.argv[1:])


if __name__ == "__main__":
    run()

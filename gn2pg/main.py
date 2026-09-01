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
from gn2pg.database.migrations import ExistingSchemaError
from gn2pg.env import CONFDIR
from gn2pg.helpers import full_download, init, manage_configs, retry_failed, update
from gn2pg.logger import setup_logging
from gn2pg.store_postgresql import PostgresqlUtils
from gn2pg.utils import BColors, validate_datetime

logger = logging.getLogger(__name__)

sh_col = BColors()


def since_datetime(value: str) -> str:
    """Validate a CLI value used as an incremental download start date."""
    try:
        return validate_datetime(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from error


def arguments(args):
    """Define and parse command arguments.

    Args:
        args ([str]): command line parameters as list of strings

    Returns:
        :obj:`argparse.Namespace`: command line parameters namespace
    """
    # Get options
    parser = argparse.ArgumentParser(description=__project__)

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
        version=f"{__project__} v{__version__}",
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
        "--upgrade",
        "--json-tables-create",
        dest="upgrade",
        help=_("Upgrade the database schema to the latest Alembic revision"),
        action="store_true",
    )
    db_group.add_argument(
        "--stamp-existing",
        help=_("Validate and stamp an existing pre-Alembic GN2PG schema"),
        action="store_true",
    )
    db_group.add_argument(
        "--status",
        help=_("Show the current and target database migration revisions"),
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
    download_group.add_argument(
        "--retry-failed",
        help=_("Resume failed API downloads without starting a new transfer"),
        action="store_true",
    )
    download_parser.add_argument(
        "--since",
        type=since_datetime,
        default=None,
        help=_("Override the incremental download start date"),
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
    args = arguments(args)
    print(epilog)

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

    logger.info(
        _("%(program)s, version %(version)s"), {"program": sys.argv[0], "version": __version__}
    )
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
            logger.critical(
                _("Incorrect content in TOML configuration %(file)s: %(error)s"),
                {"file": args.file, "error": e},
            )
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
        update(cfg_ctrl, since=args.since)

    if args.retry_failed:
        logger.info(_("Retry failed downloads"))
        retry_failed(cfg_ctrl)

    return True


def handle_database_commands(args, cfg_ctrl) -> None:
    """Handle commands related to 'config'."""

    cfg_source_list = cfg_ctrl.source_list
    cfg = list(cfg_source_list.values())[0]
    logger.info(
        _("config file have %(count)s source(s) wich are: %(sources)s"),
        {"count": len(cfg_source_list), "sources": ", ".join(cfg_source_list.keys())},
    )

    manage_pg = PostgresqlUtils(cfg)

    if args.upgrade:
        logger.info(_("Upgrade database schema"))
        manage_pg.create_json_tables()
    if args.stamp_existing:
        logger.info(_("Validate and stamp existing database schema"))
        try:
            manage_pg.stamp_existing()
        except ExistingSchemaError as error:
            logger.critical(str(error))
            raise SystemExit(1) from error
    if args.status:
        status = manage_pg.migration_status()
        logger.info(_("Schema: %s"), cfg.database.schema_import)
        logger.info(_("Current revision: %s"), (status.current or "not versioned"))
        logger.info(_("Target revision: %s"), status.head)
        logger.info(_("Pending migrations: %s"), ("yes" if status.pending else "no"))
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

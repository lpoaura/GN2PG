#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Program entry point"""

from __future__ import print_function

import argparse
import logging
import shutil
import toml
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
import sys
from toml import TomlDecodeError

import pkg_resources
from gn2gn_client import metadata

logger = logging.getLogger(__name__)
__version__ = metadata.version


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
    parser.add_argument("config", help="Configuration file name")

    return parser.parse_args(args)


def main(args):
    """Main entry point allowing external calls

    Args:
      args ([str]): command line parameter list
    """

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
    ch = logging.StreamHandler()
    # create formatter and add it to the handlers
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(module)s:%(funcName)s - %(message)s"
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

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
        init(args.config)
        return None

    # Get configuration from file
    if not (Path.home() / args.config).is_file():
        logger.critical(
            "Configuration file %s does not exist", str(Path.home() / args.config)
        )
        return None
    logger.info("Getting configuration data from %s", args.config)
    try:
        cfg_ctrl = toml.load(str(Path.home() / args.config))
    except TomlDecodeError:
        logger.critical("Incorrect content in TOML configuration %s", args.config)
        sys.exit(0)
    cfg_source_list = cfg_ctrl.SOURCES
    logger.info(cfg_source_list)

    return None


def init(config: str):
    """Copy TOML template file to home directory."""
    toml_src = pkg_resources.resource_filename(__name__, "data/gn2gnconfig.toml")
    toml_dst = str(Path.home() / config)
    logger.info("Creating TOML configuration file %s, from %s", toml_dst, toml_src)
    shutil.copyfile(toml_src, toml_dst)
    logger.info("Please edit %s before running the script", toml_dst)


def run():
    """Zero-argument entry point for use with setuptools/distribute."""
    # raise SystemExit(main(sys.argv))
    return main(sys.argv[1:])


if __name__ == "__main__":
    run()

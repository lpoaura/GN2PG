#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Main cli functions"""

import importlib.resources
import logging
import os
import shutil
import subprocess
import sys
from os import listdir
from os.path import isfile, join
from pathlib import Path
from typing import Optional

from gn2pg import _
from gn2pg.download import Data
from gn2pg.env import CONFDIR

# from gn2pg.logger import logger
from gn2pg.store_postgresql import StorePostgresql
from gn2pg.utils import BColors

sh_col = BColors()

logger = logging.getLogger(__name__)


def init(file: str) -> None:
    """Init config file from template

    Args:
        file (str): The name of the configuration file to create.
    """

    # Get the path to the template file
    toml_src = importlib.resources.files(  # pylint: disable=too-many-function-args
        __package__ or "gn2pg"
    ).joinpath(  # pylint: disable=too-many-function-args
        "data", "gn2pgconfig.toml"
    )

    toml_dst = str(CONFDIR / file)

    # Check if the destination file already exists
    if Path(toml_dst).is_file():
        CONFDIR.mkdir(exist_ok=True)
        logger.info(_("Conf directory %s created"), str(CONFDIR))
        logger.warning(_("%s file already exists"), toml_dst)

        overwrite = input(
            _(
                f"{sh_col.color('header')}Would you like to overwrite file "
                f"{toml_dst}{sh_col.color('endc')} "
                f"([{sh_col.color('bold')}y{sh_col.color('endc')}]es"
                f"/[{sh_col.color('bold')}n{sh_col.color('endc')}]o) ? "
            )
        )

        if overwrite.lower() == "n":
            logger.warning(_("File %s will be preserved"), toml_dst)
            sys.exit(0)
        else:
            logger.warning(_("file %s will be overwritten"), toml_dst)

    logger.info(_("Creating TOML configuration file %s, from %s"), toml_dst, toml_src)
    shutil.copyfile(toml_src, toml_dst)
    edit_config(toml_dst)
    sys.exit(0)


def full_download_1source(ctrl, cfg):
    """Downloads from a single controler."""

    logger.debug(cfg)
    with StorePostgresql(cfg) as store_pg:
        downloader = ctrl(cfg, store_pg)
        logger.debug(
            _("%s => Starting download using controler %s"),
            cfg.source,
            downloader.name,
        )
        downloader.store()
        logger.info(
            _("%s => Ending download using controler %s"),
            cfg.source,
            downloader.name,
        )
        downloader.exit()


def full_download(cfg_ctrl):
    """Performs a full download of all sites and controlers,
    based on configuration file."""

    logger.info(cfg_ctrl)
    cfg_source_list = cfg_ctrl.source_list
    logger.info(_("Defining full download jobs"))
    for source, cfg in cfg_source_list.items():
        if cfg.enable:
            logger.info(_("Starting full download for source %s"), source)
            full_download_1source(Data, cfg)
        else:
            logger.info(_("Source %s is disabled"), source)


def update_1source(ctrl, cfg):
    """[summary]

    Args:
        ctrl ([type]): [description]
        cfg ([type]): [description]
    """
    logger.debug(_("config source name %s"), cfg.name)
    logger.debug(_("controler %s"), ctrl)
    with StorePostgresql(cfg) as store_pg:
        downloader = ctrl(cfg, store_pg)
        logger.debug(
            _("%s => Starting update (%s)"),
            cfg.source,
            downloader.name,
        )
        downloader.update()
        logger.info(
            _("%s => Ending update (%s)"),
            cfg.name,
            downloader.name,
        )
        downloader.exit()


def update(cfg_ctrl):
    """[summary]

    Args:
        cfg_ctrl ([type]): [description]
    """
    logger.info(cfg_ctrl)
    cfg_source_list = cfg_ctrl.source_list
    logger.info(_("Defining full download jobs"))
    for source, cfg in cfg_source_list.items():
        if cfg.enable:
            logger.info(_("Starting update for source %s"), source)
            update_1source(Data, cfg)
            logger.info(_("Ending update for source %s"), source)

        else:
            logger.info(_("Source %s is disabled"), source)


def edit_config(file_path: str) -> None:
    "Open config file in a text editor"
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL") or "nano"
    subprocess.run([editor, file_path], check=False)


def manage_configs(action: str, file: Optional[str] = None):
    """Manage config files from  config directory (list, read, edit)"""
    config_files = [
        f for f in listdir(CONFDIR) if isfile(join(CONFDIR, f)) and f.endswith(".toml")
    ]
    if action == "list":
        for i, config in enumerate(config_files):
            print(config)
    print("<manage_configs> action", action)
    if action in ("read", "edit"):
        print("<file>", file)
        if file == "empty":
            for i, config in enumerate(config_files):
                print(f"{i}: {config}")
            while True:
                try:
                    config_idx = int(input(_("choose config to open : ")))
                    file = config_files[int(config_idx)]
                except ValueError:
                    print(_("Sorry, you must enter a number."))
                except IndexError:
                    print(_(f"You must enter a number between 0 and {len(config_files)-1}"))
                break
        file_path = CONFDIR / file
        if action == "read":
            with open(file_path, "r", encoding="utf-8") as config_file:
                print(config_file.read())
        else:
            edit_config(file_path)

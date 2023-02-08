#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Main cli functions"""


import logging
import logging.config
import shutil
import sys
from pathlib import Path
from subprocess import call

import pkg_resources

from gn2pg import _
from gn2pg.download import Data
from gn2pg.env import ENVDIR
from gn2pg.store_postgresql import StorePostgresql
from gn2pg.utils import BColors

logger = logging.getLogger(__name__)

sh_col = BColors()


def init(file: str) -> None:
    """Init config file from template

    Args:
        file (str): [description]
    """

    toml_src = pkg_resources.resource_filename(__name__, "data/gn2pgconfig.toml")
    toml_dst = str(ENVDIR / file)
    if Path(toml_dst).is_file():
        ENVDIR.mkdir(exist_ok=True)
        logger.info(_("Conf directory %s created"), str(ENVDIR))
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
    logger.info(_("Please edit %s before running the script"), toml_dst)
    sys.exit(0)


def edit(file: str) -> None:
    """Open editor to edit config file

    Args:
        file (str): [description]
    """
    config_file = ENVDIR / file
    call(["editor", config_file])


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
            _("%s => Starting updating using controler %s"),
            cfg.source,
            downloader.name,
        )
        downloader.update()
        logger.info(
            _("%s => Ending updating using controler %s"),
            cfg.source,
            downloader.name,
        )


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
            logger.info(_("Starting update download for source %s"), source)
            update_1source(Data, cfg)
        else:
            logger.info(_("Source %s is disabled"), source)

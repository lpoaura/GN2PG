#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Environment file"""

from pathlib import Path

CONFDIR = Path.home() / ".gn2pg"
"""Config system directory (~/.gn2pg/)"""

LOGDIR = CONFDIR / "log"
"""Log system directory (subdir of CONFDIR)"""

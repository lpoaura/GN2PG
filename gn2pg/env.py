#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Environment file"""

from pathlib import Path

ENVDIR = Path.home() / ".gn2pg"
"""Config system directory (~/.gn2pg/)"""

LOGDIR = ENVDIR / "log"
"""Log system directory (subdir of ENVDIR)"""

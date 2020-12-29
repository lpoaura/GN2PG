#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Environment file"""

from pathlib import Path

ENVDIR = Path.home() / ".gn2gn"
"""Config system directory (~/.gn2gn/)"""

LOGDIR = ENVDIR / "log"
"""Log system directory (subdir of ENVDIR)"""

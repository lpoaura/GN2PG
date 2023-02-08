#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Some utils"""

from typing import Any


class BColors:
    """Colors used for cli"""

    def __init__(self):
        self.colors = {
            "header": "[95m",
            "okblue": "[94m",
            "okcyan": "[96m",
            "okgreen": "[92m",
            "warning": "[93m",
            "fail": "[91m",
            "endc": "[0m",
            "bold": "[1m",
            "underline": "[4m",
        }

    def color(self, color: str):
        """bash shell color code"""
        color_code = self.colors[color] if color in self.colors else color
        return f"\033{color_code}"


transtable = str.maketrans(
    "àâäéèêëîïôöùûüŷÿç~- ",
    "aaaeeeeiioouuuyyc___",
    "&'([{|}])`^\\/+-=*°$£%§.?!;:<>",
)


def simplify(source: str) -> str:
    """Codify source name

    Args:
        source (str): Original source name

    Returns:
        str: Codified source name
    """
    clean_result = " ".join(source.split())
    newsource = clean_result.lower().translate(transtable)
    return newsource


def coalesce_in_dict(source: dict, key: str, default: Any) -> Any:
    """[summary]

    Args:
        source (dict): [description]
        key(str):
        default (any): [description]

    Returns:
        any: [description]
    """
    if key in source:
        return source[key]
    return default

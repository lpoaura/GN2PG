#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Some utils"""

from typing import Any


class BColors:
    """Colors used for cli"""

    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


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
    else:
        return default

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Some utils"""

import datetime
from typing import Any


class XferStatus:
    """List of transfer status"""

    # The transfer has been created but processing has not started yet.
    init = "init"
    # Data or metadata is currently being downloaded and stored.
    import_data = "importing data"
    # Records deleted from the source are currently being removed locally.
    delete = "delete"
    # All requested transfer steps completed successfully.
    success = "success"
    # The transfer stopped because an API or processing error occurred.
    failed = "failed"
    skipped = "skipped"


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
    """Coalesce function applyed on dict values

    Args:
        source (dict): Source
        key(str): key
        default (any): Default value

    Returns:
        any: Any value
    """
    if key in source:
        return source[key]
    return default


def validate_datetime(date_text: str) -> str:
    """Return an ISO date after validation."""
    try:
        datetime.date.fromisoformat(date_text)
    except ValueError as error:
        raise ValueError("incorrect date format, expected YYYY-MM-DD or YY:MM:DD hh:mm") from error
    return date_text

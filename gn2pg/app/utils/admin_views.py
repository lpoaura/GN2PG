"""Some format helpers"""

import json

from jinja2.utils import markupsafe


def json_formatter(_0, _1, model, name):
    """Prettify JSON data in flask admin lists"""
    value = getattr(model, name)
    json_value = json.dumps(value, ensure_ascii=False, indent=2)
    return markupsafe.Markup(f"<pre class='ctn-row-long-text'>{json_value}</pre>")


def add_class_ctn_row_long_text_formatter(_0, _1, model, name):
    """Prettify long text data in flask admin lists"""
    value = getattr(model, name)
    return markupsafe.Markup(f"<pre class='ctn-row-long-text'>{value}</pre>")

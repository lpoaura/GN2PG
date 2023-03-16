import json

from jinja2.utils import markupsafe


def json_formatter(view, context, model, name):
    """Prettify JSON data in flask admin lists"""
    value = getattr(model, name)
    json_value = json.dumps(value, ensure_ascii=False, indent=2)
    return markupsafe.Markup("<pre class='ctn-row-long-text'>{}</pre>".format(json_value))


def add_class_ctn_row_long_text_formatter(view, context, model, name):
    """Prettify long text data in flask admin lists"""
    value = getattr(model, name)
    return markupsafe.Markup("<pre class='ctn-row-long-text'>{}</pre>".format(value))

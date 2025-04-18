# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath("../.."))

from gn2pg import __version__, __project__

import importlib.metadata

# -- General configuration ----------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom ones.

pkg_metadata = importlib.metadata.metadata("GN2PG_client")

project = __project__
description = pkg_metadata.get("Summary")
repo_url = ", ".join(pkg_metadata.get_all("Project-URL"))
author = pkg_metadata.get("Author")
version = release = __version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.intersphinx",
    # "sphinx.ext.todo",
    "sphinx.ext.coverage",
    # "sphinx.ext.viewcode",
    "myst_parser",
]

html_logo = "_static/src_gn2pg.png"

source_suffix = {".md": "markdown", ".rst": "restructuredtext"}

html_theme_options = {
    "external_links": [
        ("Github", "https://github.com/lpoaura/GN2PG"),
        ("LPO Auvergne-Rhône-Alpes", "https://auvergne-rhone-alpes.lpo.fr/"),
    ]
}

master_doc = "index"

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "press"
# html_theme_options = {
#     "display_version": True,
#     "logo_only": False,
#     "prev_next_buttons_location": "both",
#     "style_external_links": True,
#     "style_nav_header_background": "SteelBlue",
#     # Toc options
#     "collapse_navigation": True,
#     "includehidden": False,
#     "navigation_depth": 4,
#     "sticky_navigation": False,
#     "titles_only": False,
# }

myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "html_image",
    # "linkify",
    "replacements",
    "smartquotes",
    "substitution",
]

myst_substitutions = {
    "author": author,
    "date_update": datetime.now().strftime("%d %B %Y"),
    "description": description,
    "repo_url": repo_url,
    "title": project,
    "version": version,
}

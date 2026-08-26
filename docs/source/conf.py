# Configuration file for the Sphinx documentation builder.

import sys
from pathlib import Path

# Add the parent directory to Python path for autodoc
sys.path.insert(0, str(Path(__file__).parent.parent.parent.absolute()))

# Project information
project = "odr-bootstrap"
copyright = "2025, Henry Towbin"
author = "Henry Towbin"

# Get version from package
import odr_bootstrap  # noqa: E402

release = odr_bootstrap.__version__
version = release

# Extensions
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
    "sphinx.ext.napoleon",  # Support NumPy-style docstrings
]

# AutoDoc settings
autodoc_typehints = "description"
autodoc_member_order = "bysource"
autoclass_members_are_attributes = True

# Napoleon settings (for NumPy docstring parsing)
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = False
napoleon_use_param = True
napoleon_use_keyword = True
napoleon_use_rtype = True

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
}

# HTML output
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "collapse_navigation": False,
    "sticky_navigation": True,
    "navigation_depth": 4,
    "includehidden": True,
    "logo_only": False,
    "prev_next_buttons_location": "bottom",
}

# HTML static and template paths
templates_path = ["_templates"]
html_static_path = ["_static"]

# Source file suffix
source_suffix = ".rst"

# Master doc
master_doc = "index"

# Language
language = "en"

# Highlighting
pygments_style = "sphinx"

# Suppress warnings
suppress_warnings = ["ref.python"]

# Output options
html_use_smartypants = True
html_show_sourcelink = True
html_show_sphinx = True
html_show_copyright = True

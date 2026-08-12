"""Sphinx build configuration for nexsci-rv docs."""

import os
from importlib.metadata import version as _pkg_version

# Notebooks execute at build time with no network and no credentials.
# The tutorials' first cell reads this var and patches the network call sites.
os.environ.setdefault("NEXSCI_RV_OFFLINE_FIXTURES", "1")

project = "nexsci-rv"
author = "NExScI"
copyright = "2026, California Institute of Technology"
release = _pkg_version("nexsci-rv")
version = ".".join(release.split(".")[:2])

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "myst_nb",  # provides the MyST Markdown parser; do NOT also load myst_parser
    "sphinx_copybutton",
]

# --- autodoc / napoleon (Google-style docstrings live in src/) ---
autodoc_typehints = "description"
autodoc_typehints_format = "short"
autodoc_member_order = "bysource"
autoclass_content = "class"
autodoc_default_options = {"members": True, "show-inheritance": True}
autosummary_generate = True
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_use_rtype = False

# --- intersphinx: makes astropy.table.Table / SkyCoord auto-link ---
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "astropy": ("https://docs.astropy.org/en/stable/", None),
}

# --- MyST + myst-nb ---
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "attrs_inline",
    "substitution",
    "linkify",
]
myst_heading_anchors = 4
nb_execution_mode = "auto"  # run notebooks lacking stored outputs
nb_execution_raise_on_error = True  # a broken notebook fails the build
nb_execution_timeout = 120

# --- strictness (parity with the old `mkdocs build --strict`) ---
nitpicky = True
# autodoc renders the source docstrings' type hints as cross-references. The
# names below are the package's internal type aliases and unqualified
# stdlib/astropy/own-class names that appear in those signatures; they cannot be
# resolved as links and are not worth churning the library's docstrings over.
# (Prose pages use fully-qualified roles, e.g. {py:class}`astropy.table.Table`,
# which DO resolve via intersphinx — so this does not mask real broken links.)
nitpick_ignore: list[tuple[str, str]] = [
    ("py:class", "Path"),
    ("py:class", "Table"),
    ("py:class", "NotApplicable"),
    ("py:class", "AsyncJob"),
    ("py:class", "DownloadError"),
    ("py:class", "Archive"),
    ("py:class", "CoordInput"),
    ("py:class", "RadiusInput"),
    ("py:class", "OutputFormat"),
    ("py:class", "DateRange"),
    ("py:class", "adql.CoordInput"),
    ("py:class", "adql.RadiusInput"),
    ("py:class", "requests.Session"),
    ("py:meth", "query_datetime"),
]

# github.com/Caltech-IPAC/nexsci-rv is still private pending ISG review, so
# anonymous `linkcheck` 404s on it. It becomes resolvable when ISG flips the
# repo public (step 5 of IPAC's open-sourcing process); drop this then.
linkcheck_ignore = [
    r"https://github\.com/Caltech-IPAC/nexsci-rv.*",
]

# --- theme: sphinx_rtd_theme (the theme pyNEID used) ---
html_theme = "sphinx_rtd_theme"
html_title = "nexsci-rv"
html_static_path = ["_static"]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "myst-nb",
    ".ipynb": "myst-nb",
}

exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    "**/.ipynb_checkpoints",
]

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Wordweaver'
copyright = '2024, Preston Hager'
author = 'Preston Hager'

# -- Path setup --------------------------------------------------------------
# The project directory is located at the root of the repository.
from pathlib import Path
import sys
project_path = Path(__file__).resolve().parents[2].joinpath(Path("src")).as_posix()
print("Proejct path:", project_path)
sys.path.insert(0, project_path)

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon']

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_theme_options = {
    'github_user': 'PrestonHager',
    'github_repo': 'Wordweaver',
    'github_button': True,
    'github_type': 'watch',
    'github_count': True,
    'fixed_sidebar': True,
}
html_sidebars = {
    '**': [
        'about.html',
        'navigation.html',
        'relations.html',
        'searchbox.html',
    ]
}
html_static_path = ['_static']

# Word Weaver

[![Build](https://github.com/PrestonHager/Wordweaver/actions/workflows/python-app-build.yml/badge.svg)](https://github.com/PrestonHager/Wordweaver/actions/workflows/python-app-build.yml)
[![Test](https://github.com/PrestonHager/Wordweaver/actions/workflows/python-app.yml/badge.svg)](https://github.com/PrestonHager/Wordweaver/actions/workflows/python-app.yml)
[![Documentation Status](https://readthedocs.org/projects/wordweaver-app/badge/?version=latest)](https://wordweaver-app.readthedocs.io/en/latest/?badge=latest)

Your complete toolbox for creating conlangs.

## Features

- **Phonology**: Define your conlang's phonology.
- **Grammar**: Define your conlang's grammar.
- **Word Generator**: Generate words in your conlang based on your grammar and phonology.
- **Dictionary**: Create and manage your conlang's lexicon.
- **Sound Change Applier**: Apply sound changes to words in your conlang.
- **Orthography**: Define your conlang's orthography.
- **Text**: Write and translate text in your conlang.
- **Export**: Export your conlang's data to a variety of formats.

## Installation

Download the latest release from the [releases page][0] and run the installer.
Open the application by searching for "Word Weaver" in the start menu or library.

## Development

As an open-source project, we depend on the community for feedback such as bug reports and feature requests, as well as contributions such as code and documentation.
If you would like to contribute, please follow the instructions below for setting up the development environment.
If you only plan on writing documentation, you can skip the packaging step.

### Prerequisites

- [Python 3.12+][1]
- [uv package manager][3] (recommended) or pip
- [Nix][4] (optional, for Nix Flakes development)
- [This repository][2]

### Setup

#### Option 1: Using Nix Flakes (Recommended)

If you have Nix with flakes enabled, you can set up the development environment automatically:

```bash
git clone https://github.com/PrestonHager/Wordweaver.git
cd Wordweaver
nix develop
```

This will drop you into a shell with all dependencies installed. Then install Python dependencies:

```bash
uv sync
```

#### Option 2: Using uv (without Nix)

Clone the repository and install the dependencies with uv:

```bash
git clone https://github.com/PrestonHager/Wordweaver.git
cd Wordweaver
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh  # Unix/macOS
# or: irm https://astral.sh/uv/install.ps1 | iex  # Windows

# Install dependencies
uv sync
```

#### Option 3: Using pip (legacy)

```bash
git clone https://github.com/PrestonHager/Wordweaver.git
cd Wordweaver
# Create a virtual environment and activate it
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -e .
```

### Running and Testing

To run the application:

```bash
# With uv
uv run python src/main.py

# Or with pip (after installing)
python src/main.py
```

To run the tests:

```bash
# With uv
uv run python -m unittest discover test

# Or with pip
python -m unittest discover test
```

To lint the code, use `pylint`:

```bash
# With uv
uv run pylint --rcfile=pylintrc src

# Or with pip (after installing pylint)
pylint --rcfile=pylintrc src
```

To build the documentation use the `sphinx-build` command:

```bash
# With uv
uv run sphinx-build -b html docs docs/_build

# Or with pip (after installing sphinx)
sphinx-build -b html docs docs/_build
```

### Packaging

To package the application, use the `pyinstaller` module.

```bash
# With uv
uv run python -m PyInstaller Wordweaver.spec

# Or with pip (after installing PyInstaller)
python -m PyInstaller Wordweaver.spec
```

The packaged application will be in the `dist` directory.
You can then use the built binary to run the application.

When releasing new versions, update the version number in the `VERSION` file.
The `src/VERSION` file is used only when running the application from source.
The `VERSION` file is used when packaging the application with PyInstaller.

To build an installer will depend on your operating system.
You must run the appropriate command for your system:

#### Windows

Instructions coming soon!

#### macOS

Instructions coming soon!

#### Linux

Instructions coming soon!

[0]: https://github.com/PrestonHager/Wordweaver/releases
[1]: https://www.python.org/downloads/
[2]: https://github.com/PrestonHager/Wordweaver
[3]: https://docs.astral.sh/uv/
[4]: https://nixos.org/download.html

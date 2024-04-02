# Word Weaver

[![Build](https://github.com/PrestonHager/Wordweaver/actions/workflows/python-app-build.yml/badge.svg)](https://github.com/PrestonHager/Wordweaver/actions/workflows/python-app-build.yml)
[![Test](https://github.com/PrestonHager/Wordweaver/actions/workflows/python-app.yml/badge.svg)](https://github.com/PrestonHager/Wordweaver/actions/workflows/python-app.yml)

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

- [Python][1]
- [This repository][2]

### Setup

Clone the repository and install the dependencies with pip:

```bash
git clone https://github.com/PrestonHager/Wordweaver.git
cd Wordweaver
python -m venv .venv -r requirements.txt
```

If you don't want to work in a virtual environment, you can install the dependencies globally:

```bash
python -m pip install -r requirements.txt
```

[0]: https://github.com/PrestonHager/Wordweaver/releases
[1]: https://www.python.org/downloads/
[2]: https://github.com/PrestonHager/Wordweaver

### Running and Testing

To run the application, use the `main.py` file:

```bash
python main.py
```

To run the tests, use the `unittest` module. For example, to run the tests in the `test` directory:

```bash
python -m unittest discover test
```

### Packaging

To package the application, use the `pyinstaller` module.

```bash
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

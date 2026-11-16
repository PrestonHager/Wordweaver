# scripts/make_default_project.py
#
# Rebuild src/default.wwproj, the Project a new Project starts from.
# Run it from the repo root with `uv run python scripts/make_default_project.py` whenever the file format changes.

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "src"
sys.path.append(str(SRC))

from wordweaver_project import Project

STARTER_PHONEMES = ["n", "p", "b", "d", "k", "ɾ", "f", "s", "l", "a", "e", "i", "o", "u"]

def main():
    project = Project("Untitled Project")
    language = project.add_language("Untitled Language")
    language.inventory.set_symbols(STARTER_PHONEMES)
    project.save(SRC / "default.wwproj")

if __name__ == "__main__":
    main()

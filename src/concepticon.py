# concepticon.py

"""Concepticon concepts, for Concept References and for seeding a Lexicon from a concept list.

Concepticon (https://concepticon.clld.org) links the concepts in published word lists, like the Swadesh 100, to one shared set of concept sets.
Its data is licensed CC-BY 4.0. Each list in concept_lists/ says where it came from and who to credit.
"""

import csv
import json
import re
import shutil
import urllib.request
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from lexicon import ConceptReference, ConceptSource
from senses import NotDownloadedError, Sense

CONCEPTICON_VERSION = "v3.4.0"
CONCEPTICON_URL = f"https://raw.githubusercontent.com/concepticon/concepticon-data/{CONCEPTICON_VERSION}/concepticondata/concepticon.tsv"
# The concept lists that ship with the app. PyInstaller puts them next to the modules too.
LISTS_DIR = Path(__file__).parent / "concept_lists"

@dataclass(frozen=True)
class Concept:
    """One Concepticon concept set, like 948 WATER, as it shows up in a concept list."""
    id: str
    gloss: str
    definition: str = ""
    # The list's own English word for it, like "fat (grease)", and where it sits in the list.
    english: str = ""
    number: str = ""

    @property
    def reference(self) -> ConceptReference:
        return ConceptReference(ConceptSource.CONCEPTICON, self.id)

    @property
    def seed_gloss(self) -> str:
        """The Gloss a seeded Entry gets.

        The list's English word reads better than Concepticon's capitals, like "warm (hot)" for HOT OR WARM.
        """
        return self.english or self.gloss.lower()

@dataclass(frozen=True)
class ConceptList:
    """A published list of concepts, like the Swadesh 100, in its own order."""
    id: str
    name: str
    concepts: tuple[Concept, ...]
    source: str = ""
    license: str = ""
    attribution: str = ""

    @classmethod
    def load(cls, path: str | Path) -> "ConceptList":
        """Read a list from a JSON file like the ones in concept_lists/.

        :raises OSError: If the file can't be read.
        :raises ValueError: If it isn't a concept list.
        """
        with open(path, encoding="utf-8") as f_in:
            data = json.load(f_in)
        try:
            concepts = tuple(Concept(str(c["id"]), c["gloss"], c.get("definition", ""), c.get("english", ""), str(c.get("number", ""))) for c in data["concepts"])
            return cls(data["id"], data.get("name", data["id"]), concepts, data.get("source", ""), data.get("license", ""), data.get("attribution", ""))
        except (KeyError, TypeError) as e:
            raise ValueError(f"{path} isn't a concept list") from e

    def __len__(self) -> int:
        return len(self.concepts)

    def __iter__(self):
        return iter(self.concepts)

def concept_lists(folder: str | Path=LISTS_DIR) -> list[ConceptList]:
    """Every concept list in `folder`, which is the ones that ship with the app by default, sorted by name."""
    return sorted((ConceptList.load(path) for path in Path(folder).glob("*.json")), key=lambda concept_list: concept_list.name)

class ConcepticonSenses:
    """Every Concepticon concept set, searchable by gloss, so a Definition can link to one.

    The table is about 500 KB, so it's downloaded on request into the user's data folder instead of shipping with the app.
    """

    download_note = "It needs an internet connection, it's about 500 KB, and it only happens once."

    def __init__(self, path: str | Path | None=None, url: str=CONCEPTICON_URL, name: str="Concepticon"):
        """
        :param path: str | Path | None: Where the table is kept. Defaults to the user's data folder.
        :param url: str: Where to download the table from, which is the pinned Concepticon release.
        """
        self.source = ConceptSource.CONCEPTICON
        self.name = name
        self._path = Path(path) if path is not None else None
        self._url = url
        self._senses: dict[str, Sense] | None = None

    def is_downloaded(self) -> bool:
        return self._file().exists()

    def download(self):
        file = self._file()
        file.parent.mkdir(parents=True, exist_ok=True)
        # Download to another name first, so a broken download never looks finished.
        partial = file.with_name(file.name + ".part")
        with urllib.request.urlopen(self._url, timeout=60) as response, open(partial, "wb") as f_out:
            shutil.copyfileobj(response, f_out)
        partial.replace(file)
        self._senses = None

    def search(self, lemma: str) -> list[Sense]:
        """Concepts with this word in their gloss. An exact match comes first, then shorter glosses.

        "water" finds WATER, then things like BOILED WATER, but not WATERFALL.
        """
        key = _fold(lemma)
        if not key:
            return []
        matches = []
        for sense in self._all().values():
            gloss = _fold(sense.lemmas[0])
            if gloss == key:
                matches.append((0, len(gloss), sense))
            elif re.search(rf"\b{re.escape(key)}\b", gloss):
                matches.append((1, len(gloss), sense))
        return [sense for *_rank, sense in sorted(matches, key=lambda match: match[:2])]

    def get(self, id: str) -> Sense | None:
        return self._all().get(id.strip())

    def _file(self) -> Path:
        if self._path is None:
            from platformdirs import user_data_path
            self._path = user_data_path("Wordweaver", False) / "concepticon" / f"concepticon-{CONCEPTICON_VERSION}.tsv"
        return self._path

    def _all(self) -> dict[str, Sense]:
        if self._senses is None:
            if not self.is_downloaded():
                raise NotDownloadedError(f"{self.name} hasn't been downloaded yet")
            self._senses = {sense.id: sense for sense in _read_table(self._file())}
        return self._senses

_lookup: ConcepticonSenses | None = None

def concepticon_lookup() -> ConcepticonSenses:
    """The app's one Concepticon lookup. Making it doesn't load anything, that waits for the first search."""
    global _lookup
    if _lookup is None:
        _lookup = ConcepticonSenses()
    return _lookup

def _read_table(path: Path) -> Iterable[Sense]:
    # Concepticon's tables are tab separated with no quoting, so quotes in a definition are just quotes.
    with open(path, encoding="utf-8-sig", newline="") as f_in:
        for row in csv.DictReader(f_in, delimiter="\t", quoting=csv.QUOTE_NONE):
            if not row.get("ID") or not row.get("GLOSS"):
                continue
            # The ontological category, like Person/Thing, stands in for a part of speech.
            yield Sense(ConceptSource.CONCEPTICON, row["ID"], (row["GLOSS"],), (row.get("ONTOLOGICAL_CATEGORY") or "").lower(), row.get("DEFINITION") or "")

def _fold(text: str) -> str:
    return " ".join(text.split()).casefold()

__all__ = ["CONCEPTICON_URL", "CONCEPTICON_VERSION", "Concept", "ConceptList", "ConcepticonSenses", "LISTS_DIR", "concept_lists", "concepticon_lookup"]

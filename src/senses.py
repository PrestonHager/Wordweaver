# senses.py

"""Search open dictionaries for senses to link to Definitions as Concept References.

Nothing here loads dictionary data until the first search, so the app starts quickly.
The real data is downloaded on request, never bundled with the app.
"""

import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from lexicon import ConceptReference, ConceptSource

# Part of speech codes as wordnets write them, with names to show in the UI.
POS_NAMES = {
    "n": "noun",
    "v": "verb",
    "a": "adjective",
    "s": "adjective",
    "r": "adverb",
    "c": "conjunction",
    "p": "adposition",
    "x": "other",
    "u": "unknown",
}

@dataclass(frozen=True)
class Sense:
    """One exact sense in an open dictionary, like an Open English WordNet synset."""
    source: ConceptSource
    id: str
    lemmas: tuple[str, ...]
    pos: str
    gloss: str

    @property
    def reference(self) -> ConceptReference:
        """The Concept Reference that links a Definition to this sense."""
        return ConceptReference(self.source, self.id)

    @property
    def pos_name(self) -> str:
        return POS_NAMES.get(self.pos, self.pos)

    def label(self) -> str:
        """A short line to show in a list, like "bank (noun): sloping land beside a body of water"."""
        return f"{', '.join(self.lemmas)} ({self.pos_name}): {self.gloss}"

class SenseLookup(Protocol):
    """Searches one open dictionary. The data loads lazily, on the first search or get."""
    source: ConceptSource
    name: str

    def is_downloaded(self) -> bool:
        """Whether the data is on this computer. Searching before then raises NotDownloadedError."""
        ...

    def download(self):
        """Fetch the data. This can take a while, so the UI runs it off the main thread."""
        ...

    def search(self, lemma: str) -> list[Sense]:
        """Every sense with this lemma, most common first where the dictionary knows."""
        ...

    def get(self, id: str) -> Sense | None:
        """The sense with this ID, or None if there isn't one."""
        ...

class NotDownloadedError(Exception):
    """The dictionary data hasn't been downloaded yet."""

class MemorySenses:
    """A small dictionary held in memory, mostly for tests. `load` is only called on the first search or get."""

    def __init__(self, load: Callable[[], Iterable[Sense]], source: ConceptSource=ConceptSource.OPEN_ENGLISH_WORDNET, name: str="Test Senses"):
        self.source = source
        self.name = name
        self._load = load
        self._senses: dict[str, Sense] | None = None

    @classmethod
    def from_json(cls, path: str | Path, source: ConceptSource=ConceptSource.OPEN_ENGLISH_WORDNET) -> "MemorySenses":
        """Read senses from a JSON list of objects with `id`, `lemmas`, `pos`, and `gloss`."""
        def load():
            with open(path, encoding="utf-8") as f_in:
                return [Sense(source, s["id"], tuple(s["lemmas"]), s["pos"], s["gloss"]) for s in json.load(f_in)]
        return cls(load, source, Path(path).stem)

    @property
    def is_loaded(self) -> bool:
        return self._senses is not None

    def is_downloaded(self) -> bool:
        return True

    def download(self):
        pass

    def search(self, lemma: str) -> list[Sense]:
        key = _fold(lemma)
        if not key:
            return []
        return [sense for sense in self._all().values() if any(_fold(l) == key for l in sense.lemmas)]

    def get(self, id: str) -> Sense | None:
        return self._all().get(id)

    def _all(self) -> dict[str, Sense]:
        if self._senses is None:
            self._senses = {sense.id: sense for sense in self._load()}
        return self._senses

class WordNetSenses:
    """Open English WordNet, through the `wn` package, kept in the user's data folder.

    `wn` is only imported on first use, since it's slow to import and the data is big.
    """

    def __init__(self, lexicon: str="oewn:2025", data_dir: str | Path | None=None, name: str="Open English WordNet"):
        self.source = ConceptSource.OPEN_ENGLISH_WORDNET
        self.name = name
        self._lexicon = lexicon
        self._data_dir = data_dir
        self._wordnet = None

    def is_downloaded(self) -> bool:
        wn = self._wn()
        return bool(wn.lexicons(lexicon=self._lexicon))

    def download(self):
        wn = self._wn()
        # No progress bar, since a windowed app may not have a console for it to write to.
        cache_path = wn.download(self._lexicon, progress_handler=None)
        # Now the data is in wn's database, so the downloaded archive is just taking up space.
        Path(cache_path).unlink(missing_ok=True)

    def search(self, lemma: str) -> list[Sense]:
        lemma = lemma.strip()
        if not lemma:
            return []
        return [self._sense(synset) for synset in self._open().synsets(lemma)]

    def get(self, id: str) -> Sense | None:
        wn = self._wn()
        try:
            return self._sense(self._open().synset(id))
        except wn.Error:
            return None

    def _open(self):
        if self._wordnet is None:
            if not self.is_downloaded():
                raise NotDownloadedError(f"{self.name} hasn't been downloaded yet")
            self._wordnet = self._wn().Wordnet(self._lexicon)
        return self._wordnet

    def _sense(self, synset) -> Sense:
        return Sense(self.source, synset.id, tuple(synset.lemmas()), synset.pos, synset.definition() or "")

    def _wn(self):
        import wn
        from platformdirs import user_data_path
        data_dir = self._data_dir or user_data_path("Wordweaver", False) / "wordnet"
        if wn.config.data_directory != Path(data_dir).expanduser().resolve():
            wn.config.data_directory = data_dir
        # The download runs on a worker thread, then searches run on the main thread, so the database has to allow both.
        wn.config.allow_multithreading = True
        return wn

# One lookup per dictionary, made the first time it's asked for.
_lookups: dict[str, SenseLookup] = {}

def lookup_for(gloss_language: str) -> SenseLookup | None:
    """The dictionary to search for a Gloss Language, or None if there isn't one for it yet.

    Making the lookup doesn't load anything, that waits for the first search.
    """
    primary = gloss_language.split("-")[0].lower()
    # TODO: other Gloss Languages search Open Multilingual Wordnet in #48.
    if primary != "en":
        return None
    if "oewn" not in _lookups:
        _lookups["oewn"] = WordNetSenses()
    return _lookups["oewn"]

def _fold(text: str) -> str:
    # Wordnets write multi-word lemmas with spaces or underscores, and case doesn't matter for a search.
    return " ".join(text.replace("_", " ").split()).casefold()

__all__ = ["MemorySenses", "NotDownloadedError", "POS_NAMES", "Sense", "SenseLookup", "WordNetSenses", "lookup_for"]

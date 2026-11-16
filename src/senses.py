# senses.py

"""Search open dictionaries for senses to link to Definitions as Concept References.

Nothing here loads dictionary data until the first search, so the app starts quickly.
The real data is downloaded on request, never bundled with the app.
"""

import json
import re
import warnings
from collections.abc import Callable, Iterable
from contextlib import contextmanager
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
        # Some wordnets have no definition for a sense, so then the lemmas have to do.
        if not self.gloss:
            return f"{', '.join(self.lemmas)} ({self.pos_name})"
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
        config = wn.config  # pyright: ignore[reportPrivateImportUsage]  wn documents config but leaves it out of __all__.
        if config.data_directory != Path(data_dir).expanduser().resolve():
            config.data_directory = data_dir
        # The download runs on a worker thread, then searches run on the main thread, so the database has to allow both.
        config.allow_multithreading = True
        return wn

# Gloss Languages with a wordnet in Open Multilingual Wordnet, by their primary language subtag.
# Each one has a name to show and the `wn` lexicon to download. English uses Open English WordNet instead.
OMW_VERSION = "2.0"
OMW_LANGUAGES = {
    "ar": ("Arabic", "omw-arb"),
    "bg": ("Bulgarian", "omw-bg"),
    "ca": ("Catalan", "omw-ca"),
    "da": ("Danish", "omw-da"),
    "el": ("Greek", "omw-el"),
    "es": ("Spanish", "omw-es"),
    "eu": ("Basque", "omw-eu"),
    "fi": ("Finnish", "omw-fi"),
    "fr": ("French", "omw-fr"),
    "gl": ("Galician", "omw-gl"),
    "he": ("Hebrew", "omw-he"),
    "hr": ("Croatian", "omw-hr"),
    "id": ("Indonesian", "omw-id"),
    "is": ("Icelandic", "omw-is"),
    # NOTE: Italian has two wordnets in OMW. MultiWordNet is the bigger one, so we use it over ItalWordNet.
    "it": ("Italian", "omw-it"),
    "ja": ("Japanese", "omw-ja"),
    "lt": ("Lithuanian", "omw-lt"),
    "ms": ("Malay", "omw-zsm"),
    "nb": ("Norwegian Bokmål", "omw-nb"),
    "nl": ("Dutch", "omw-nl"),
    "nn": ("Norwegian Nynorsk", "omw-nn"),
    "pl": ("Polish", "omw-pl"),
    "pt": ("Portuguese", "omw-pt"),
    "ro": ("Romanian", "omw-ro"),
    "sk": ("Slovak", "omw-sk"),
    "sl": ("Slovenian", "omw-sl"),
    "sq": ("Albanian", "omw-sq"),
    "sv": ("Swedish", "omw-sv"),
    "th": ("Thai", "omw-th"),
    "zh": ("Chinese", "omw-cmn"),
}
# Other codes people might type for the same languages, like the ISO 639-3 codes OMW uses itself.
_LANGUAGE_ALIASES = {"arb": "ar", "cmn": "zh", "zsm": "ms", "no": "nb", "nob": "nb", "nno": "nn"}

# The Collaborative Interlingual Index, which gives every concept an ID and an English definition shared by all wordnets.
CILI = "cili:1.0"
_ILI_ID = re.compile(r"i\d+")

def omw_gloss(definition: str | None, english_definition: str | None) -> str:
    """The gloss to show for an OMW sense.

    Most OMW wordnets have no definitions of their own, so we fall back to the ILI's English one, marked as English.
    With neither, it's empty and the sense just shows its lemmas.
    """
    if definition:
        return definition
    if english_definition:
        return f"(English) {english_definition}"
    return ""

class OmwSenses(WordNetSenses):
    """One language's wordnet from Open Multilingual Wordnet, through the `wn` package.

    Senses are identified by their ILI ID, like `i85041`, so a link points at the same concept in every language.
    A synset without an ILI falls back to its own synset ID, like `omw-fr-09213565-n`.
    """

    def __init__(self, lexicon: str, name: str, data_dir: str | Path | None=None):
        super().__init__(lexicon, data_dir, name)
        self.source = ConceptSource.OPEN_MULTILINGUAL_WORDNET

    def is_downloaded(self) -> bool:
        with _quiet():
            return super().is_downloaded() and self._ili_downloaded()

    def download(self):
        wn = self._wn()
        with _quiet():
            if not wn.lexicons(lexicon=self._lexicon):
                super().download()
        # The ILI file is only a few MB, and it's what gives us English definitions.
        if not self._ili_downloaded():
            Path(wn.download(CILI, progress_handler=None)).unlink(missing_ok=True)

    def get(self, id: str) -> Sense | None:
        wn = self._wn()
        try:
            if _ILI_ID.fullmatch(id):
                synsets = self._open().synsets(ili=id)
                return self._sense(synsets[0]) if synsets else None
            return self._sense(self._open().synset(id))
        except wn.Error:
            return None

    def _open(self):
        with _quiet():
            return super()._open()

    def _sense(self, synset) -> Sense:
        english = self._english_definition(synset.ili) if synset.ili else None
        gloss = omw_gloss(synset.definition(), english)
        return Sense(self.source, synset.ili or synset.id, tuple(synset.lemmas()), synset.pos, gloss)

    def _english_definition(self, ili_id: str) -> str | None:
        from wn import ili
        found = ili.get(ili_id)
        return found.definition() if found else None

    def _ili_downloaded(self) -> bool:
        from wn import ili
        # Before the ILI file is added, wn still knows the IDs the wordnets use, but not their status or definitions.
        found = ili.get("i1")
        return found is not None and found.status == "active"

@contextmanager
def _quiet():
    # OMW wordnets say they need the OMW English wordnet for their relations.
    # We only use their lemmas, so wn's warning about it is just noise.
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="lexicon dependencies not available")
        yield

def wordnet_languages() -> list[tuple[str, str]]:
    """Every Gloss Language with a wordnet to search, as (name, code), with English first."""
    others = sorted((language[0], code) for code, language in OMW_LANGUAGES.items())
    return [("English", "en"), *others]

# One lookup per dictionary, made the first time it's asked for.
_lookups: dict[str, SenseLookup] = {}

def lookup_for(gloss_language: str) -> SenseLookup | None:
    """The dictionary to search for a Gloss Language, or None if there's no wordnet for it.

    Making the lookup doesn't load anything, that waits for the first search.
    """
    primary = gloss_language.split("-")[0].lower()
    primary = _LANGUAGE_ALIASES.get(primary, primary)
    if primary == "en":
        if "oewn" not in _lookups:
            _lookups["oewn"] = WordNetSenses()
        return _lookups["oewn"]
    if primary not in OMW_LANGUAGES:
        return None
    name, lexicon = OMW_LANGUAGES[primary]
    if lexicon not in _lookups:
        _lookups[lexicon] = OmwSenses(f"{lexicon}:{OMW_VERSION}", f"Open Multilingual Wordnet ({name})")
    return _lookups[lexicon]

def _fold(text: str) -> str:
    # Wordnets write multi-word lemmas with spaces or underscores, and case doesn't matter for a search.
    return " ".join(text.replace("_", " ").split()).casefold()

__all__ = ["CILI", "MemorySenses", "NotDownloadedError", "OMW_LANGUAGES", "OMW_VERSION", "OmwSenses", "POS_NAMES", "Sense", "SenseLookup",
           "WordNetSenses", "lookup_for", "omw_gloss", "wordnet_languages"]

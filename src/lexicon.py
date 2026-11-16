# lexicon.py

import unicodedata
from collections.abc import Callable, Iterable, Iterator

class Form:
    """How an Entry is said, as a sequence of Phonemes written as IPA symbols."""

    def __init__(self, phonemes: Iterable[str]=()):
        self._phonemes = tuple(phonemes)

    @classmethod
    def parse(cls, text: str, symbols: Iterable[str]=()) -> "Form":
        """Split IPA text into Phonemes, matching the longest of `symbols` first.

        Anything that doesn't match one of `symbols` becomes one Phoneme per letter, keeping any combining marks with it.
        Spaces are ignored.
        """
        symbols = sorted({s for s in symbols if s}, key=len, reverse=True)
        text = "".join(text.split())
        phonemes = []
        i = 0
        while i < len(text):
            # First, try the Language's own Phonemes, so things like affricates stay in one piece.
            match = next((s for s in symbols if text.startswith(s, i)), None)
            if match is None:
                # Otherwise take one letter, plus any combining marks right after it.
                end = i + 1
                while end < len(text) and unicodedata.combining(text[end]):
                    end += 1
                match = text[i:end]
            phonemes.append(match)
            i += len(match)
        return cls(phonemes)

    @property
    def phonemes(self) -> tuple[str, ...]:
        return self._phonemes

    def __str__(self) -> str:
        return "".join(self._phonemes)

    def __repr__(self) -> str:
        return f"<Form /{self}/>"

    def __eq__(self, other) -> bool:
        return isinstance(other, Form) and self._phonemes == other._phonemes

    def __hash__(self) -> int:
        return hash(self._phonemes)

    def __len__(self) -> int:
        return len(self._phonemes)

class Definition:
    """One precise meaning of an Entry.

    It has an ordered list of Glosses, and optionally some technical linguistic terms and a free-text description.
    """

    def __init__(self, id: int, glosses: Iterable[str], terms: Iterable[str]=(), description: str=""):
        # Definitions are made and changed by the Lexicon, which hands out the ID.
        self._id = id
        self._glosses = tuple(glosses)
        self._terms = tuple(terms)
        self._description = description

    @property
    def id(self) -> int:
        return self._id

    @property
    def glosses(self) -> tuple[str, ...]:
        return self._glosses

    @property
    def terms(self) -> tuple[str, ...]:
        """Technical linguistic terms, like "plural" or "inalienable", in order."""
        return self._terms

    @property
    def description(self) -> str:
        return self._description

    def __repr__(self) -> str:
        return f"<Definition {self.id}: {'; '.join(self.glosses)}>"

class Entry:
    """One item in a Lexicon, with one Form and one or more Definitions in order."""

    def __init__(self, id: int, form: Form, definitions: Iterable[Definition]):
        # Entries are made and changed by the Lexicon, which hands out the ID.
        self._id = id
        self._form = form
        self._definitions = list(definitions)

    @property
    def id(self) -> int:
        return self._id

    @property
    def form(self) -> Form:
        return self._form

    @property
    def definitions(self) -> list[Definition]:
        return list(self._definitions)

    @property
    def glosses(self) -> tuple[str, ...]:
        """The Glosses of every Definition, in order."""
        return tuple(gloss for definition in self._definitions for gloss in definition.glosses)

    @property
    def etymons(self) -> tuple:
        # TODO: Etymons come with the Descent spec. Until then every Entry is a Coinage.
        return ()

    @property
    def is_coinage(self) -> bool:
        return not self.etymons

    def __repr__(self) -> str:
        return f"<Entry {self.id} /{self.form}/: {'; '.join(self.glosses)}>"

class Lexicon:
    """A Language's dictionary of Entries, kept in the order they were added."""

    def __init__(self, new_id: Callable[[], int]):
        """
        :param new_id: Callable[[], int]: Gives out a new record ID each time it's called, so IDs are unique in the Project.
        """
        self._new_id = new_id
        self._entries: dict[int, Entry] = {}

    def add(self, form: Form | str, glosses: Iterable[str], terms: Iterable[str]=(), description: str="") -> Entry:
        """Add an Entry with a Form and one Definition. Use add_definition to give it more.

        A Form given as a string is split one letter at a time; use Form.parse to match a Phoneme Inventory.

        :raises ValueError: If there isn't at least one Gloss.
        """
        # Check the Glosses before handing out any IDs.
        glosses = _clean_glosses(glosses)
        entry_id = self._new_id()
        entry = Entry(entry_id, _to_form(form), [self._new_definition(glosses, terms, description)])
        self._entries[entry.id] = entry
        return entry

    def edit(self, entry: Entry, form: Form | str | None=None, glosses: Iterable[str] | None=None):
        """Change an Entry's Form, the Glosses of its first Definition, or both. IDs stay the same.

        Use edit_definition to change any other Definition.

        :raises KeyError: If the Entry isn't in this Lexicon.
        :raises ValueError: If `glosses` is given but has no Gloss in it. The Entry isn't changed then.
        """
        self._check(entry)
        if glosses is not None:
            entry._definitions[0]._glosses = _clean_glosses(glosses)
        if form is not None:
            entry._form = _to_form(form)

    def remove(self, entry: Entry):
        """Remove an Entry and its Definitions. Their IDs are never handed out again.

        :raises KeyError: If the Entry isn't in this Lexicon.
        """
        self._check(entry)
        del self._entries[entry.id]

    def add_definition(self, entry: Entry, glosses: Iterable[str], terms: Iterable[str]=(), description: str="", index: int | None=None) -> Definition:
        """Give an Entry another Definition, at the end or at `index`.

        :raises KeyError: If the Entry isn't in this Lexicon.
        :raises ValueError: If there isn't at least one Gloss.
        """
        self._check(entry)
        definition = self._new_definition(glosses, terms, description)
        entry._definitions.insert(len(entry._definitions) if index is None else index, definition)
        return definition

    def edit_definition(self, entry: Entry, definition: Definition, glosses: Iterable[str] | None=None, terms: Iterable[str] | None=None, description: str | None=None):
        """Change a Definition's Glosses, technical terms, or description. Anything left as None stays the same.

        :raises KeyError: If the Entry isn't in this Lexicon, or the Definition isn't on the Entry.
        :raises ValueError: If `glosses` is given but has no Gloss in it. The Definition isn't changed then.
        """
        self._check_definition(entry, definition)
        if glosses is not None:
            definition._glosses = _clean_glosses(glosses)
        if terms is not None:
            definition._terms = _clean_terms(terms)
        if description is not None:
            definition._description = description.strip()

    def remove_definition(self, entry: Entry, definition: Definition):
        """Remove one of an Entry's Definitions. Its ID is never handed out again.

        :raises KeyError: If the Entry isn't in this Lexicon, or the Definition isn't on the Entry.
        :raises ValueError: If it's the Entry's last Definition, since every Entry needs one.
        """
        self._check_definition(entry, definition)
        if len(entry._definitions) == 1:
            raise ValueError("An Entry needs at least one Definition")
        entry._definitions.remove(definition)

    def move_definition(self, entry: Entry, definition: Definition, index: int):
        """Move one of an Entry's Definitions to `index`, shifting the others along.

        :raises KeyError: If the Entry isn't in this Lexicon, or the Definition isn't on the Entry.
        """
        self._check_definition(entry, definition)
        entry._definitions.remove(definition)
        entry._definitions.insert(index, definition)

    def get(self, id: int) -> Entry | None:
        return self._entries.get(id)

    def _check(self, entry: Entry):
        if self._entries.get(entry.id) is not entry:
            raise KeyError(f"Entry {entry.id} isn't in this Lexicon")

    def _check_definition(self, entry: Entry, definition: Definition):
        self._check(entry)
        if not any(d is definition for d in entry._definitions):
            raise KeyError(f"Definition {definition.id} isn't on Entry {entry.id}")

    def _new_definition(self, glosses: Iterable[str], terms: Iterable[str], description: str) -> Definition:
        return Definition(self._new_id(), _clean_glosses(glosses), _clean_terms(terms), description.strip())

    def _restore(self, entry: Entry):
        # Put back an Entry loaded from a file, keeping its IDs.
        self._entries[entry.id] = entry

    def __iter__(self) -> Iterator[Entry]:
        return iter(list(self._entries.values()))

    def __len__(self) -> int:
        return len(self._entries)

    def __contains__(self, entry: Entry) -> bool:
        return self._entries.get(entry.id) is entry

def _to_form(form: Form | str) -> Form:
    return form if isinstance(form, Form) else Form.parse(form)

def _clean_glosses(glosses: Iterable[str]) -> tuple[str, ...]:
    # Drop blank Glosses, so an empty line in the editor doesn't turn into one.
    glosses = tuple(g.strip() for g in glosses if g.strip())
    if not glosses:
        raise ValueError("A Definition needs at least one Gloss")
    return glosses

def _clean_terms(terms: Iterable[str]) -> tuple[str, ...]:
    # Technical terms are optional, so blank ones are just dropped.
    return tuple(t.strip() for t in terms if t.strip())

__all__ = ["Definition", "Entry", "Form", "Lexicon"]

# lexicon.py

import unicodedata
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from enum import Enum, IntEnum

from phonology import is_valid_phoneme
from tags import Tag, Tags

# Tie bars join two letters into one sound, like the affricate /t͡s/.
_TIE_BARS = "͜͡"

class Form:
    """How an Entry is said, as a sequence of Phonemes written as IPA symbols."""

    def __init__(self, phonemes: Iterable[str]=()):
        self._phonemes = tuple(phonemes)

    @classmethod
    def parse(cls, text: str, symbols: Iterable[str]=()) -> "Form":
        """Split IPA text into Phonemes, matching the longest of `symbols` first.

        Anything that doesn't match one of `symbols` becomes one Phoneme per letter, keeping any combining marks with it.
        Letters joined by a tie bar, like t͡s, stay together.
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
                # A tie bar is a combining mark too, so when one ends the run we take the next letter with it.
                end = i + 1
                while end < len(text) and unicodedata.combining(text[end]):
                    end += 1
                    if text[end - 1] in _TIE_BARS and end < len(text):
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

@dataclass(frozen=True)
class FormCheck:
    """What check_form found in a Form. It's only a warning, so nothing here stops an Entry being saved.

    `unknown` has the IPA Phonemes that aren't in the Phoneme Inventory, and `invalid` has the text that isn't an IPA consonant or vowel.
    Both are in the order they first show up in the Form, without repeats.
    """
    unknown: tuple[str, ...] = ()
    invalid: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.unknown and not self.invalid

def check_form(form: Form | str, symbols: Iterable[str]) -> FormCheck:
    """Check a Form against a Phoneme Inventory, given as its IPA symbols.

    A Form given as a string is split with Form.parse using the same symbols.
    An empty Form always passes, since unfinished Entries have one.
    """
    symbols = set(symbols)
    if not isinstance(form, Form):
        form = Form.parse(form, symbols)
    unknown = {}
    invalid = {}
    for phoneme in form.phonemes:
        if phoneme in symbols:
            continue
        # Use the same check as the Phoneme Inventory, so anything flagged as unknown can be added to it.
        if is_valid_phoneme(phoneme):
            unknown[phoneme] = None
        else:
            invalid[phoneme] = None
    return FormCheck(tuple(unknown), tuple(invalid))

class SearchField(Enum):
    """What part of an Entry a Lexicon search looks at."""
    FORM = "Form"
    GLOSS = "Gloss"
    DESCRIPTION = "Description"

    def __str__(self) -> str:
        return self.value

class SortOrder(Enum):
    """How a Lexicon search orders the Entries it finds."""
    BEST_MATCH = "Best match"
    FORM = "Form"
    GLOSS = "Gloss"

    def __str__(self) -> str:
        return self.value

class ConceptSource(IntEnum):
    """An open dictionary that a Concept Reference can point into."""
    # The values match the ConceptSource enum in the .proto, so they can be saved as is.
    OPEN_ENGLISH_WORDNET = 1
    OPEN_MULTILINGUAL_WORDNET = 2
    # TODO: Concepticon comes in #49. It's here so its value stays reserved.
    CONCEPTICON = 3

    @property
    def prefix(self) -> str:
        """A short name for the source, used when a reference is written out as text."""
        return _SOURCE_PREFIXES[self]

    @classmethod
    def from_prefix(cls, prefix: str) -> "ConceptSource":
        """:raises ValueError: If no source has that prefix."""
        for source, known in _SOURCE_PREFIXES.items():
            if known == prefix:
                return source
        raise ValueError(f"No Concept Reference source is called {prefix!r}")

_SOURCE_PREFIXES = {
    ConceptSource.OPEN_ENGLISH_WORDNET: "oewn",
    ConceptSource.OPEN_MULTILINGUAL_WORDNET: "omw",
    ConceptSource.CONCEPTICON: "concepticon",
}

@dataclass(frozen=True)
class ConceptReference:
    """A link from a Definition to one exact sense in an open dictionary, like an Open English WordNet synset.

    It's the source plus that source's own stable ID, such as `oewn-09213565-n`.
    """
    source: ConceptSource
    id: str

    def __post_init__(self):
        if not isinstance(self.source, ConceptSource):
            raise ValueError(f"{self.source!r} isn't a Concept Reference source")
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("A Concept Reference needs an ID")
        # The dataclass is frozen, so this is how we tidy the ID.
        object.__setattr__(self, "id", self.id.strip())

    @classmethod
    def parse(cls, text: str) -> "ConceptReference":
        """Read a reference written as `source:id`, like `oewn:oewn-09213565-n`.

        :raises ValueError: If the text isn't in that shape, or the source isn't known.
        """
        prefix, colon, id = text.partition(":")
        if not colon:
            raise ValueError(f"{text!r} isn't a Concept Reference")
        return cls(ConceptSource.from_prefix(prefix.strip()), id)

    def __str__(self) -> str:
        return f"{self.source.prefix}:{self.id}"

class Definition:
    """One precise meaning of an Entry.

    It has an ordered list of Glosses, and optionally some technical linguistic terms, a free-text description, and a Concept Reference.
    """

    def __init__(self, id: int, glosses: Iterable[str], terms: Iterable[str]=(), description: str="", concept_reference: ConceptReference | None=None):
        # Definitions are made and changed by the Lexicon, which hands out the ID.
        self._id = id
        self._glosses = tuple(glosses)
        self._terms = tuple(terms)
        self._description = description
        self._concept_reference = concept_reference

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

    @property
    def concept_reference(self) -> ConceptReference | None:
        """The exact dictionary sense this Definition means, if one is linked."""
        return self._concept_reference

    def __repr__(self) -> str:
        return f"<Definition {self.id}: {'; '.join(self.glosses)}>"

class Entry:
    """One item in a Lexicon, with one Form and one or more Definitions in order."""

    def __init__(self, id: int, form: Form, definitions: Iterable[Definition], tag_ids: Iterable[int]=()):
        # Entries are made and changed by the Lexicon, which hands out the ID.
        self._id = id
        self._form = form
        # Tags belong to the Project, so an Entry only keeps their IDs, in the order they were added.
        self._tag_ids = list(dict.fromkeys(tag_ids))
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
    def tag_ids(self) -> tuple[int, ...]:
        """The IDs of this Entry's Tags. Look them up in the Project's Tags to get their names."""
        return tuple(self._tag_ids)

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

    def __init__(self, new_id: Callable[[], int], tags: Tags | None=None):
        """
        :param new_id: Callable[[], int]: Gives out a new record ID each time it's called, so IDs are unique in the Project.
        :param tags: Tags | None: The Project's Tags. If given, only those Tags can go on Entries.
        """
        self._new_id = new_id
        self._entries: dict[int, Entry] = {}
        self._tags = tags

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

    def set_concept_reference(self, entry: Entry, definition: Definition, reference: ConceptReference):
        """Link a Definition to one exact sense in an open dictionary, replacing any link it had.

        :raises KeyError: If the Entry isn't in this Lexicon, or the Definition isn't on the Entry.
        :raises ValueError: If `reference` isn't a ConceptReference.
        """
        self._check_definition(entry, definition)
        if not isinstance(reference, ConceptReference):
            raise ValueError(f"{reference!r} isn't a Concept Reference")
        definition._concept_reference = reference

    def clear_concept_reference(self, entry: Entry, definition: Definition):
        """Unlink a Definition from its dictionary sense. Nothing happens if it wasn't linked.

        :raises KeyError: If the Entry isn't in this Lexicon, or the Definition isn't on the Entry.
        """
        self._check_definition(entry, definition)
        definition._concept_reference = None

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

    @property
    def tags(self) -> Tags | None:
        """The Project's Tags, which every Language shares."""
        return self._tags

    def tag(self, entry: Entry, tag: Tag):
        """Put a Tag on an Entry. Nothing happens if it's already there.

        :raises KeyError: If the Entry isn't in this Lexicon, or the Tag isn't in the Project.
        """
        self._check(entry)
        if self._tags is not None and tag not in self._tags:
            raise KeyError(f"Tag {tag.id} isn't in this Project")
        if tag.id not in entry._tag_ids:
            entry._tag_ids.append(tag.id)

    def untag(self, entry: Entry, tag: Tag):
        """Take a Tag off an Entry. Nothing happens if it wasn't there.

        :raises KeyError: If the Entry isn't in this Lexicon.
        """
        self._check(entry)
        if tag.id in entry._tag_ids:
            entry._tag_ids.remove(tag.id)

    def tagged(self, tag: Tag) -> list[Entry]:
        """Find every Entry with a Tag, in Lexicon order."""
        return [entry for entry in self._entries.values() if tag.id in entry._tag_ids]

    def search(self, text: str="", field: SearchField=SearchField.GLOSS, tag: Tag | None=None, sort: SortOrder=SortOrder.BEST_MATCH) -> list[Entry]:
        """Find the Entries whose Form, Gloss, or Definition description matches `text`, optionally only those with `tag`.

        Forms match the IPA text as typed, ignoring spaces. Glosses and descriptions ignore case.
        An Entry matches a Gloss or description search if any of its Definitions does.
        Blank `text` matches every Entry, so this also lists or sorts the whole Lexicon.

        With SortOrder.BEST_MATCH, exact matches come first, then ones that start with `text`, then ones that only contain it.
        SortOrder.FORM puts empty Forms last, and SortOrder.GLOSS goes by the first Gloss of the first Definition.
        Ties stay in Lexicon order.
        """
        query = _search_key(text, field)
        entries = self._entries.values() if tag is None else self.tagged(tag)
        # First, rank every Entry against the query, and drop the ones that don't match at all.
        ranked = []
        for entry in entries:
            rank = 0
            if query:
                ranks = [_match_rank(query, value) for value in _search_values(entry, field)]
                rank = min((r for r in ranks if r is not None), default=None)
                if rank is None:
                    continue
            ranked.append((rank, entry))
        # Then put them in the order that was asked for. Python's sort is stable, so ties keep Lexicon order.
        if sort is SortOrder.FORM:
            ranked.sort(key=lambda pair: (not pair[1].form, _search_key(str(pair[1].form), SearchField.FORM)))
        elif sort is SortOrder.GLOSS:
            ranked.sort(key=lambda pair: _search_key(pair[1].definitions[0].glosses[0], SearchField.GLOSS))
        else:
            ranked.sort(key=lambda pair: pair[0])
        return [entry for _rank, entry in ranked]

    def homophones_of(self, form: Form | str, exclude: Entry | None=None) -> list[Entry]:
        """Every Entry with exactly this Form, other than `exclude`, in the order they were added.

        Call it before adding or editing an Entry to warn about Homophones. It never stops the save.
        An empty Form never matches, since unfinished Entries (like seeded ones) all have one.
        """
        form = _to_form(form)
        if not form:
            return []
        return [e for e in self._entries.values() if e.form == form and e is not exclude]

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

def _search_key(text: str, field: SearchField) -> str:
    # Normalize the Unicode so a letter typed with a combining mark matches the same letter typed precomposed.
    text = unicodedata.normalize("NFC", text)
    if field is SearchField.FORM:
        # Forms ignore spaces like Form.parse does, but IPA cares about case, so that's kept.
        return "".join(text.split())
    return " ".join(text.split()).casefold()

def _search_values(entry: Entry, field: SearchField) -> list[str]:
    if field is SearchField.FORM:
        values = [str(entry.form)]
    elif field is SearchField.GLOSS:
        values = list(entry.glosses)
    else:
        values = [d.description for d in entry.definitions]
    return [_search_key(value, field) for value in values]

def _match_rank(query: str, value: str) -> int | None:
    # Lower is better: 0 is exact, 1 starts with the query, 2 only contains it, and None doesn't match.
    if value == query:
        return 0
    if value.startswith(query):
        return 1
    if query in value:
        return 2
    return None

def _clean_glosses(glosses: Iterable[str]) -> tuple[str, ...]:
    # Drop blank Glosses, so an empty line in the editor doesn't turn into one.
    glosses = tuple(g.strip() for g in glosses if g.strip())
    if not glosses:
        raise ValueError("A Definition needs at least one Gloss")
    return glosses

def _clean_terms(terms: Iterable[str]) -> tuple[str, ...]:
    # Technical terms are optional, so blank ones are just dropped.
    return tuple(t.strip() for t in terms if t.strip())

__all__ = ["ConceptReference", "ConceptSource", "Definition", "Entry", "Form", "FormCheck", "Lexicon", "SearchField", "SortOrder", "check_form"]

# phoneme_classes.py

from collections.abc import Callable
from dataclasses import dataclass

from ipapy.ipachar import IPAChar

from phonology import Phoneme, PhonemeInventory

def _consonant(test: Callable[[IPAChar], bool]) -> Callable[[IPAChar], bool]:
    return lambda c: c.is_consonant and test(c)

def _vowel(test: Callable[[IPAChar], bool]) -> Callable[[IPAChar], bool]:
    return lambda c: c.is_vowel and test(c)

def _is_sonorant(c: IPAChar) -> bool:
    # Vowels, nasals, approximants, trills, and flaps, but not lateral fricatives or affricates.
    if c.is_vowel:
        return True
    return c.is_consonant and c.manner.split("-")[-1] in ("nasal", "approximant", "trill", "flap")

@dataclass(frozen=True)
class DefaultClass:
    key: str
    name: str
    test: Callable[[IPAChar], bool]

# The Classes every Language starts with, filled in from each Phoneme's IPA features.
# NOTE: a default Class's ID is its place in this list, so only ever add to the end.
DEFAULT_CLASSES = [
    DefaultClass("consonant", "Consonant", lambda c: c.is_consonant),
    DefaultClass("vowel", "Vowel", lambda c: c.is_vowel),
    DefaultClass("sonorant", "Sonorant", _is_sonorant),
    DefaultClass("obstruent", "Obstruent", lambda c: c.is_consonant and not _is_sonorant(c)),
    DefaultClass("nasal", "Nasal", _consonant(lambda c: c.manner == "nasal")),
    DefaultClass("stop", "Stop", _consonant(lambda c: c.manner in ("plosive", "implosive", "ejective"))),
    DefaultClass("fricative", "Fricative", _consonant(lambda c: c.manner.endswith("fricative"))),
    DefaultClass("affricate", "Affricate", _consonant(lambda c: c.manner.endswith("affricate"))),
    DefaultClass("sibilant", "Sibilant", _consonant(lambda c: c.manner.startswith("sibilant"))),
    DefaultClass("approximant", "Approximant", _consonant(lambda c: c.manner.endswith("approximant"))),
    DefaultClass("trill", "Trill", _consonant(lambda c: c.manner == "trill")),
    DefaultClass("tap", "Tap", _consonant(lambda c: c.manner.endswith("flap"))),
    DefaultClass("lateral", "Lateral", _consonant(lambda c: c.manner.startswith("lateral"))),
    DefaultClass("click", "Click", _consonant(lambda c: c.manner.endswith("click"))),
    DefaultClass("implosive", "Implosive", _consonant(lambda c: c.manner == "implosive")),
    DefaultClass("ejective", "Ejective", _consonant(lambda c: "ejective" in c.manner)),
    DefaultClass("voiced", "Voiced", _consonant(lambda c: c.voicing == "voiced")),
    DefaultClass("voiceless", "Voiceless", _consonant(lambda c: c.voicing == "voiceless")),
    DefaultClass("labial", "Labial", _consonant(lambda c: "labi" in c.place)),
    DefaultClass("coronal", "Coronal", _consonant(lambda c: any(p in c.place for p in ("dent", "alveol", "retroflex", "linguo")))),
    DefaultClass("dorsal", "Dorsal", _consonant(lambda c: any(p in c.place for p in ("palat", "velar", "uvul")))),
    DefaultClass("laryngeal", "Laryngeal", _consonant(lambda c: c.place == "glottal" or "pharyngeal" in c.place)),
    DefaultClass("close", "Close", _vowel(lambda c: c.height in ("close", "near-close"))),
    DefaultClass("mid", "Mid", _vowel(lambda c: c.height in ("close-mid", "mid", "open-mid"))),
    DefaultClass("open", "Open", _vowel(lambda c: c.height in ("open", "near-open"))),
    DefaultClass("front", "Front", _vowel(lambda c: c.backness in ("front", "near-front"))),
    DefaultClass("central", "Central", _vowel(lambda c: c.backness == "central")),
    DefaultClass("back", "Back", _vowel(lambda c: c.backness in ("back", "near-back"))),
    DefaultClass("rounded", "Rounded", _vowel(lambda c: c.roundness == "rounded")),
    DefaultClass("unrounded", "Unrounded", _vowel(lambda c: c.roundness == "unrounded")),
]

# How many IDs each Language holds back for its default Classes, so there's room to add more later.
DEFAULT_CLASS_ID_BLOCK = 64
assert len(DEFAULT_CLASSES) <= DEFAULT_CLASS_ID_BLOCK

class PhonemeClass:
    """A named group of Phonemes in one Language. Classes overlap, so a Phoneme can be in many."""

    def __init__(self, id: int, name: str, inventory: PhonemeInventory, default: DefaultClass | None=None, check_name: Callable[[str, "PhonemeClass"], None]=lambda name, cls: None):
        self._id = id
        self._name = name
        self._check_name = check_name
        self._inventory = inventory
        self._default = default
        # The IDs of the Phonemes in this Class, once it's been edited by hand.
        # Untouched default Classes leave this as None and work out their Phonemes from IPA features.
        self._member_ids: set[int] | None = None if default is not None else set()

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str):
        """Rename the Class.

        :raises ValueError: If the name is empty or another Class in the Language has it.
        """
        self._check_name(name, self)
        self._name = name

    @property
    def is_default(self) -> bool:
        return self._default is not None

    @property
    def is_renamed(self) -> bool:
        return self.is_default and self._name != self._default.name

    @property
    def is_hand_edited(self) -> bool:
        """Whether the Phonemes in a default Class were changed by hand, so it's no longer filled in from IPA features."""
        return self.is_default and self._member_ids is not None

    def add(self, symbol: str):
        """Put a Phoneme from the inventory into this Class.

        :raises KeyError: If the Phoneme isn't in the inventory.
        """
        phoneme = self._inventory.get(symbol)
        if phoneme is None:
            raise KeyError(symbol)
        self._edit_by_hand()
        self._member_ids.add(phoneme.id)

    def remove(self, symbol: str):
        """Take a Phoneme out of this Class. It stays in the inventory."""
        phoneme = self._inventory.get(symbol)
        self._edit_by_hand()
        if phoneme is not None:
            self._member_ids.discard(phoneme.id)

    def _edit_by_hand(self):
        # The first hand edit to a default Class freezes what's in it now, so new Phonemes don't get added by themselves.
        if self._member_ids is None:
            self._member_ids = {p.id for p in self.phonemes}

    def _restore_members(self, phoneme_ids: list[int]):
        # Put back the Phonemes saved for a hand-made or hand-edited Class.
        self._member_ids = set(phoneme_ids)

    @property
    def phonemes(self) -> list[Phoneme]:
        """The Class's Phonemes, in inventory order."""
        if self._member_ids is None:
            return [p for p in self._inventory if self._default.test(p.ipa)]
        return [p for p in self._inventory if p.id in self._member_ids]

    @property
    def symbols(self) -> list[str]:
        return [p.symbol for p in self.phonemes]

    def __contains__(self, symbol: str) -> bool:
        return symbol in self.symbols

    def __repr__(self) -> str:
        return f"<PhonemeClass {self.id} {self.name!r}: {', '.join(self.symbols)}>"

class PhonemeClasses:
    """All the Phoneme Classes in one Language: the defaults first, then the user's own."""

    def __init__(self, inventory: PhonemeInventory, new_id: Callable[[], int], default_ids_start: int):
        self._inventory = inventory
        self._new_id = new_id
        self.default_ids_start = default_ids_start
        self._classes = [PhonemeClass(default_ids_start + i, d.name, inventory, d, self._check_name) for i, d in enumerate(DEFAULT_CLASSES)]

    def add(self, name: str) -> PhonemeClass:
        """Make a new, empty Class.

        :raises ValueError: If the name is empty or another Class has it.
        """
        self._check_name(name, None)
        return self._restore(self._new_id(), name)

    def remove(self, phoneme_class: PhonemeClass):
        """Delete one of the user's own Classes.

        :raises ValueError: If it's a default Class, or isn't in this Language.
        """
        if phoneme_class.is_default:
            raise ValueError("Default Phoneme Classes can't be deleted")
        self._classes.remove(phoneme_class)

    def default(self, key: str) -> PhonemeClass | None:
        return next((c for c in self._classes if c.is_default and c._default.key == key), None)

    def _restore(self, id: int, name: str) -> PhonemeClass:
        # Put back a user Class, keeping its ID.
        phoneme_class = PhonemeClass(id, name, self._inventory, None, self._check_name)
        self._classes.append(phoneme_class)
        return phoneme_class

    def _check_name(self, name: str, phoneme_class: PhonemeClass | None):
        if not name:
            raise ValueError("A Phoneme Class needs a name")
        if any(c.name == name and c is not phoneme_class for c in self._classes):
            raise ValueError(f"There's already a Phoneme Class called {name}")

    def get(self, name: str) -> PhonemeClass | None:
        return next((c for c in self._classes if c.name == name), None)

    def of(self, symbol: str) -> list[PhonemeClass]:
        """Get every Class a Phoneme is in."""
        return [c for c in self._classes if symbol in c]

    def __iter__(self):
        return iter(list(self._classes))

    def __len__(self) -> int:
        return len(self._classes)

__all__ = ["DEFAULT_CLASSES", "DEFAULT_CLASS_ID_BLOCK", "PhonemeClass", "PhonemeClasses"]

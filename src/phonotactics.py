# phonotactics.py

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from enum import Enum

from lexicon import Form
from phoneme_classes import PhonemeClass, PhonemeClasses
from phonology import PhonemeInventory

class SyllablePart(Enum):
    """The three parts of a syllable."""
    ONSET = "Onset"
    NUCLEUS = "Nucleus"
    CODA = "Coda"

    def __str__(self) -> str:
        return self.value

def parse_notation(notation: str) -> list[tuple[str, bool]]:
    """Read a Syllable Structure like "(C)V(C)" into its positions, as (label, optional) pairs.

    Each position is a Phoneme Class label, a capital letter that can be followed by small letters or digits.
    Parentheses around one label make that position optional. Spaces are ignored.

    :raises ValueError: If the notation is empty or isn't written right.
    """
    text = "".join(notation.split())
    if not text:
        raise ValueError("A Syllable Structure needs at least one position, like V")
    positions = []
    i = 0
    while i < len(text):
        optional = text[i] == "("
        if optional:
            i += 1
        # First, read one label: a capital letter, then any small letters or digits.
        if i >= len(text) or not (text[i].isalpha() and text[i].isupper()):
            found = text[i] if i < len(text) else "the end"
            raise ValueError(f"Expected a Phoneme Class label like C or V, but found {found!r} in {notation.strip()!r}")
        end = i + 1
        while end < len(text) and ((text[end].isalpha() and text[end].islower()) or text[end].isdigit()):
            end += 1
        label = text[i:end]
        i = end
        # Then the closing parenthesis, if it's optional.
        if optional:
            if i < len(text) and text[i].isalpha() and text[i].isupper():
                raise ValueError(f"Put each optional position in its own parentheses, like (C)(C), in {notation.strip()!r}")
            if i >= len(text) or text[i] != ")":
                raise ValueError(f"A parenthesis isn't closed in {notation.strip()!r}")
            i += 1
        positions.append((label, optional))
    return positions

def write_notation(positions: list[tuple[str, bool]]) -> str:
    """Write positions back as notation, like "(C)V(C)"."""
    return "".join(f"({label})" if optional else label for label, optional in positions)

@dataclass(frozen=True)
class Position:
    """One position in a Syllable Structure, which holds one Phoneme from its Phoneme Class.

    `phoneme_class` is None when no Class has the label anymore, and `part` is None when the structure has no Nucleus.
    """
    label: str
    optional: bool
    phoneme_class: PhonemeClass | None
    part: SyllablePart | None

class SyllableStructure:
    """The allowed shape of a syllable, written like (C)V(C).

    It's stored as its notation, so the labels are looked up again each time it's used.
    """

    def __init__(self, id: int, phonotactics: "Phonotactics", notation: str):
        self._id = id
        self._phonotactics = phonotactics
        self._notation = notation

    @property
    def id(self) -> int:
        return self._id

    @property
    def notation(self) -> str:
        return self._notation

    @notation.setter
    def notation(self, notation: str):
        """Change the structure.

        :raises ValueError: If the notation isn't written right, names a label no Class has, or has no Nucleus.
        """
        self._notation = self._phonotactics._check_notation(notation, self)

    @property
    def positions(self) -> list[Position]:
        """The positions in order, each with its Phoneme Class and which part of the syllable it's in."""
        parsed = parse_notation(self._notation)
        classes = [self._phonotactics._classes.with_label(position[0]) for position in parsed]
        # The Nucleus is the first run of positions for vowel Classes, everything before it is the Onset, and everything after is the Coda.
        def is_vowel_class(phoneme_class: PhonemeClass | None) -> bool:
            return phoneme_class is not None and phoneme_class.holds_vowels
        start = next((i for i, c in enumerate(classes) if is_vowel_class(c)), None)
        if start is None:
            return [Position(label, optional, c, None) for (label, optional), c in zip(parsed, classes)]
        end = start
        while end < len(classes) and is_vowel_class(classes[end]):
            end += 1
        parts = [SyllablePart.ONSET] * start + [SyllablePart.NUCLEUS] * (end - start) + [SyllablePart.CODA] * (len(classes) - end)
        return [Position(label, optional, c, part) for (label, optional), c, part in zip(parsed, classes, parts)]

    def part(self, part: SyllablePart) -> list[Position]:
        """Get the positions in the Onset, Nucleus, or Coda."""
        return [p for p in self.positions if p.part is part]

    @property
    def problem(self) -> str | None:
        """Why the structure can't be used right now, or None if it can.

        This happens when a Class it names is removed or relabelled, or its Nucleus Class stops holding vowels.
        Structures with a problem are skipped when splitting Forms into syllables.
        """
        return self._phonotactics._problem(parse_notation(self._notation), self.positions)

    def __str__(self) -> str:
        return self._notation

    def __repr__(self) -> str:
        return f"<SyllableStructure {self.id} {self._notation}>"

@dataclass(frozen=True)
class Syllable:
    """One syllable of a Form, and how it fits its Syllable Structure.

    `positions` says which position of the structure each Phoneme fills, and `parts` which part of the syllable it's in.
    """
    phonemes: tuple[str, ...]
    structure: SyllableStructure
    positions: tuple[int, ...]
    parts: tuple[SyllablePart, ...]

    def _in(self, part: SyllablePart) -> tuple[str, ...]:
        return tuple(p for p, q in zip(self.phonemes, self.parts) if q is part)

    @property
    def onset(self) -> tuple[str, ...]:
        return self._in(SyllablePart.ONSET)

    @property
    def nucleus(self) -> tuple[str, ...]:
        return self._in(SyllablePart.NUCLEUS)

    @property
    def coda(self) -> tuple[str, ...]:
        return self._in(SyllablePart.CODA)

    def __str__(self) -> str:
        return "".join(self.phonemes)

def write_syllables(syllables: list[Syllable]) -> str:
    """Write syllables with breaks between them, like ta.sta."""
    return ".".join(str(s) for s in syllables)

@dataclass(frozen=True)
class Violation:
    """Something a Form breaks in the Phonotactics.

    `syllable` is the index of the syllable it happened in, or None when it's about the whole Form.
    Each kind of rule has its own subclass, so you can tell them apart with isinstance.
    """
    message: str
    syllable: int | None = None

@dataclass(frozen=True)
class CantSyllabify(Violation):
    """The Form can't be split into syllables that fit any of the Syllable Structures."""

class Phonotactics:
    """A Language's rules for how its Phonemes combine: its Syllable Structures for now.

    You can edit the rules, split a Form into syllables, and check a Form to get back what it breaks.
    """

    def __init__(self, inventory: PhonemeInventory, classes: PhonemeClasses, new_id: Callable[[], int]):
        self._inventory = inventory
        self._classes = classes
        self._new_id = new_id
        self._structures: list[SyllableStructure] = []

    @property
    def syllable_structures(self) -> list[SyllableStructure]:
        return list(self._structures)

    def add_syllable_structure(self, notation: str) -> SyllableStructure:
        """Add a Syllable Structure written like (C)V(C).

        :raises ValueError: If the notation isn't written right, names a label no Class has, has no Nucleus, or is already there.
        """
        notation = self._check_notation(notation, None)
        return self._restore(self._new_id(), notation)

    def remove_syllable_structure(self, structure: SyllableStructure):
        """
        :raises ValueError: If the structure isn't in this Language.
        """
        self._structures.remove(structure)

    def syllabify(self, form: Form | str | tuple[str, ...]) -> list[Syllable] | None:
        """Split a Form into syllables by maximal Onset, or return None if it can't be split.

        Each syllable has to fit one of the Syllable Structures. When there's more than one way to split it,
        consonants between two Nuclei go to the Onset of the second syllable whenever the structures allow it.
        An empty Form splits into no syllables.
        """
        phonemes = self._phonemes(form)
        count = len(phonemes)
        # First, gather the structures we can use, with each position's Phonemes as a set so matching is quick.
        usable = []
        for structure in self._structures:
            positions = structure.positions
            if self._problem(parse_notation(structure.notation), positions) is None:
                phoneme_sets = []
                for position in positions:
                    phoneme_class = position.phoneme_class
                    if phoneme_class is None:
                        break
                    phoneme_sets.append(set(phoneme_class.symbols))
                else:
                    usable.append((structure, positions, phoneme_sets))
        if not usable:
            return [] if count == 0 else None
        longest = max(len(item[1]) for item in usable)
        matches: dict[tuple[int, int], Syllable | None] = {}

        def match(start: int, end: int) -> Syllable | None:
            # Find the first structure that phonemes[start:end] fits, remembering the answer.
            if (start, end) not in matches:
                matches[start, end] = self._match(phonemes[start:end], usable)
            return matches[start, end]

        # Now work backwards to find where a split can finish from.
        can_finish = [False] * (count + 1)
        can_finish[count] = True
        for start in reversed(range(count)):
            can_finish[start] = any(can_finish[end] and match(start, end) is not None for end in range(start + 1, min(count, start + longest) + 1))
        if not can_finish[0]:
            return None
        # Finally, take the shortest syllable that still lets the rest split.
        # That leaves as many Phonemes as possible for the next Onset, which is what maximal Onset means.
        syllables = []
        start = 0
        while start < count:
            end = next(end for end in range(start + 1, min(count, start + longest) + 1) if can_finish[end] and match(start, end) is not None)
            syllables.append(match(start, end))
            start = end
        return syllables

    def check(self, form: Form | str) -> list[Violation]:
        """Check a Form against the Phonotactics and get back everything it breaks. An empty list means it passes.

        An empty Form always passes, since unfinished Entries have one.
        """
        phonemes = self._phonemes(form)
        syllables = self.syllabify(phonemes)
        if syllables is None:
            text = "".join(phonemes)
            if not any(s.problem is None for s in self._structures):
                return [CantSyllabify(f"/{text}/ can't be split into syllables, since there aren't any Syllable Structures that can be used")]
            return [CantSyllabify(f"/{text}/ can't be split into syllables that fit the Syllable Structures")]
        # NOTE: later rules, like Phonotactic Constraints, add their own Violations here.
        return []

    def _phonemes(self, form: Form | str | tuple[str, ...]) -> tuple[str, ...]:
        if isinstance(form, Form):
            return form.phonemes
        if isinstance(form, str):
            return Form.parse(form, self._inventory.symbols).phonemes
        return tuple(form)

    def _match(self, phonemes: tuple[str, ...], usable) -> Syllable | None:
        for structure, positions, sets in usable:
            filled = _fill(phonemes, positions, sets)
            if filled is not None:
                return Syllable(phonemes, structure, filled, tuple(positions[i].part for i in filled))
        return None

    def _problem(self, parsed: list[tuple[str, bool]], positions: list[Position]) -> str | None:
        unknown = [position[0] for position, parsed_position in zip(parsed, positions) if parsed_position.phoneme_class is None]
        if unknown:
            return f"No Phoneme Class is labelled {', '.join(dict.fromkeys(unknown))}"
        nucleus = [p for p in positions if p.part is SyllablePart.NUCLEUS]
        if not nucleus:
            return "It needs a Nucleus, a position for a Class of vowels like V"
        if all(p.optional for p in nucleus):
            return "Its Nucleus can't be optional"
        return None

    def _check_notation(self, notation: str, structure: SyllableStructure | None) -> str:
        # Write it out tidily, then make sure it can be used right away.
        parsed = parse_notation(notation)
        notation = write_notation(parsed)
        probe = SyllableStructure(0, self, notation)
        problem = probe.problem
        if problem is not None:
            raise ValueError(f"{notation} can't be used. {problem}")
        if any(s.notation == notation and s is not structure for s in self._structures):
            raise ValueError(f"There's already a Syllable Structure {notation}")
        return notation

    def _restore(self, id: int, notation: str) -> SyllableStructure:
        # Put back a structure, keeping its ID. Loaded ones aren't checked, since a Class might have been relabelled since.
        structure = SyllableStructure(id, self, notation)
        self._structures.append(structure)
        return structure

    def __iter__(self) -> Iterator[SyllableStructure]:
        return iter(list(self._structures))

def _fill(phonemes: tuple[str, ...], positions: list[Position], sets: list[set[str]]) -> tuple[int, ...] | None:
    # Put each Phoneme in a position, left to right, skipping optional positions when we have to.
    # Return which position each Phoneme went in, or None if they don't fit.
    def walk(p: int, s: int) -> tuple[int, ...] | None:
        if s == len(phonemes):
            return () if all(position.optional for position in positions[p:]) else None
        if p == len(positions):
            return None
        if phonemes[s] in sets[p]:
            rest = walk(p + 1, s + 1)
            if rest is not None:
                return (p,) + rest
        if positions[p].optional:
            return walk(p + 1, s)
        return None
    return walk(0, 0)

__all__ = ["CantSyllabify", "Phonotactics", "Position", "Syllable", "SyllablePart", "SyllableStructure", "Violation", "parse_notation", "write_notation", "write_syllables"]

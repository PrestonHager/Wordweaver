# phonotactics.py

from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from enum import Enum, IntEnum
import math
import random

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

class SyllablePosition(IntEnum):
    """Where a syllable occurs in a Form."""
    ANY = 0
    FIRST = 1
    MIDDLE = 2
    LAST = 3
    ONLY = 4
    NON_FIRST = 5

class ConstraintMode(IntEnum):
    """Whether a Phonotactic Constraint bans or allows its sequence."""
    BAN = 0
    ALLOW = 1

class ConstraintAtom:
    """One Phoneme or Phoneme Class in a Phonotactic Constraint."""

    def __init__(self, value: str, is_class: bool):
        self.value = value
        self.is_class = is_class

    def matches(self, symbol: str, phonotactics: "Phonotactics") -> bool:
        if self.is_class:
            phoneme_class = phonotactics._classes.with_label(self.value) or phonotactics._classes.get(self.value)
            return phoneme_class is not None and symbol in phoneme_class
        return symbol == self.value

    def __str__(self) -> str:
        return self.value

class PhonotacticConstraint:
    """A rule banning a sequence in a part and/or position of a Form."""

    def __init__(self, id: int, phonotactics: "Phonotactics", atoms: tuple[ConstraintAtom, ...],
                 part: SyllablePart | None, position: SyllablePosition, across_boundaries: bool,
                 mode: ConstraintMode):
        self._id = id
        self._phonotactics = phonotactics
        self.atoms = atoms
        self.part = part
        self.position = position
        self.across_boundaries = across_boundaries
        self.mode = mode

    @property
    def id(self) -> int:
        return self._id

    def __str__(self) -> str:
        sequence = " ".join(str(atom) for atom in self.atoms)
        location = str(self.part) if self.part is not None else "anywhere"
        positions = {
            SyllablePosition.ANY: "any syllable",
            SyllablePosition.FIRST: "the first syllable",
            SyllablePosition.MIDDLE: "a middle syllable",
            SyllablePosition.LAST: "the last syllable",
            SyllablePosition.ONLY: "the only syllable",
            SyllablePosition.NON_FIRST: "a non-first syllable",
        }
        action = "only allow" if self.mode is ConstraintMode.ALLOW else "ban"
        return f"{action} {sequence} in {location.lower()} of {positions[self.position]}"

    def matches(self, syllables: list["Syllable"]) -> bool:
        if not syllables or not self.atoms:
            return False
        selected = [
            syllable for index, syllable in enumerate(syllables)
            if self.position is SyllablePosition.ANY
            or self.position is SyllablePosition.FIRST and index == 0
            or self.position is SyllablePosition.LAST and index == len(syllables) - 1
            or self.position is SyllablePosition.ONLY and len(syllables) == 1
            or self.position is SyllablePosition.MIDDLE and 0 < index < len(syllables) - 1
            or self.position is SyllablePosition.NON_FIRST and index > 0
        ]
        if not selected:
            return False
        if self.mode is ConstraintMode.ALLOW:
            for syllable in selected:
                sequence = syllable.phonemes if self.part is None else syllable._in(self.part)
                if len(sequence) != len(self.atoms) or not all(
                    atom.matches(symbol, self._phonotactics)
                    for atom, symbol in zip(self.atoms, sequence)
                ):
                    return True
            return False
        if self.part is None:
            if self.across_boundaries:
                if self.position is SyllablePosition.ANY:
                    starts = [0]
                else:
                    starts = [index for index, syllable in enumerate(syllables) if syllable in selected]
                sequences = [tuple(symbol for syllable in syllables[start:] for symbol in syllable.phonemes) for start in starts]
            else:
                sequences = [syllable.phonemes for syllable in selected]
        else:
            sequences = [tuple(syllable._in(self.part)) for syllable in selected]
        return any(
            any(all(atom.matches(symbol, self._phonotactics) for atom, symbol in zip(self.atoms, sequence[start:start + len(self.atoms)]))
                for start in range(len(sequence) - len(self.atoms) + 1))
            for sequence in sequences
        )

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
        self._constraints: list[PhonotacticConstraint] = []

    @property
    def syllable_structures(self) -> list[SyllableStructure]:
        return list(self._structures)

    @property
    def constraints(self) -> list[PhonotacticConstraint]:
        return list(self._constraints)

    def add_constraint(self, atoms: list[ConstraintAtom] | tuple[ConstraintAtom, ...],
                       part: SyllablePart | None = None, position: SyllablePosition = SyllablePosition.ANY,
                       across_boundaries: bool = True, mode: ConstraintMode = ConstraintMode.BAN) -> PhonotacticConstraint:
        if not atoms:
            raise ValueError("A Phonotactic Constraint needs at least one Phoneme or Phoneme Class")
        if any(not atom.value for atom in atoms):
            raise ValueError("A Phonotactic Constraint can't contain an empty Phoneme or Phoneme Class")
        for atom in atoms:
            if atom.is_class:
                if self._classes.with_label(atom.value) is None and self._classes.get(atom.value) is None:
                    raise ValueError(f"{atom.value} isn't a Phoneme Class in this Language")
            elif self._inventory.get(atom.value) is None:
                raise ValueError(f"{atom.value} isn't a Phoneme in this Language")
        constraint = PhonotacticConstraint(self._new_id(), self, tuple(atoms), part, position, across_boundaries, mode)
        self._constraints.append(constraint)
        return constraint

    def remove_constraint(self, constraint: PhonotacticConstraint):
        self._constraints.remove(constraint)

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
        violations = []
        for constraint in self._constraints:
            if constraint.matches(syllables):
                violations.append(Violation(f"/{''.join(phonemes)}/ breaks Phonotactic Constraint: {constraint}"))
        return violations

    def generate_forms(self, count: int, syllable_range: tuple[int, int] = (1, 3),
                       seed: int | None = None, attempt_limit: int | None = None,
                       existing: Iterable[Form] = ()) -> list[Form]:
        """Generate distinct Forms that pass this Language's Phonotactics.

        ``syllable_range`` is an inclusive minimum and maximum. Forms in ``existing`` are
        skipped, and ``seed`` makes the batch repeatable. A ValueError is raised when
        the requested batch cannot be produced before the attempt limit.
        """
        if count < 0:
            raise ValueError("The number of Forms can't be negative")
        minimum, maximum = syllable_range
        if minimum < 1 or maximum < minimum:
            raise ValueError("The syllable range must start at 1 and end at or after it")
        if count == 0:
            return []
        if attempt_limit is None:
            attempt_limit = max(100, count * 100)
        if attempt_limit < 1:
            raise ValueError("The attempt limit must be positive")
        usable = [s for s in self._structures if s.problem is None]
        if not usable:
            raise ValueError("Can't generate Forms: this Language has no usable Syllable Structures")
        weights = self._inventory.weights()
        if not weights or any(not position.phoneme_class.symbols
                              for structure in usable for position in structure.positions
                              if not position.optional and position.phoneme_class is not None):
            raise ValueError("Can't generate Forms: a required position has no Phonemes")
        found = set(existing or ())
        result: list[Form] = []
        rng = random.Random(seed)
        for _ in range(attempt_limit):
            if len(result) == count:
                return result
            chosen = [rng.choice(usable) for _ in range(rng.randint(minimum, maximum))]
            variants = [self._generation_variants(structure, rng) for structure in chosen]
            generated_syllables = self._generate_syllables(chosen, variants, weights, rng, found)
            if generated_syllables is None:
                continue
            form = Form(symbol for syllable in generated_syllables for symbol in syllable.phonemes)
            if form not in found:
                found.add(form)
                result.append(form)
                if len(result) == count:
                    return result
        raise ValueError(f"Couldn't generate {count} Forms in {attempt_limit} attempts; "
                         "the Phonotactics may allow too few Forms")

    def _generation_variants(self, structure: SyllableStructure, rng: random.Random) -> list[list[int]]:
        """Return every optional-position choice for a structure in random order."""
        optional = [i for i, position in enumerate(structure.positions) if position.optional]
        variants: list[list[int]] = []
        for mask in range(1 << len(optional)):
            skipped = {position for bit, position in enumerate(optional) if mask & (1 << bit)}
            variants.append([i for i in range(len(structure.positions)) if i not in skipped])
        rng.shuffle(variants)
        return variants

    def _generate_syllables(self, structures: list[SyllableStructure], variants: list[list[list[int]]],
                            weights: dict[str, float], rng: random.Random,
                            excluded: set[Form] | None = None) -> list[Syllable] | None:
        """Find one valid set of syllables for selected structures by backtracking."""
        selected: list[tuple[SyllableStructure, list[int]]] = []

        def choose_variants(index: int) -> list[Syllable] | None:
            if index == len(variants):
                return fill_phonemes(0, [])
            structure = structures[index]
            for positions in variants[index]:
                selected.append((structure, positions))
                answer = choose_variants(index + 1)
                selected.pop()
                if answer is not None:
                    return answer
            return None

        def fill_phonemes(index: int, syllables: list[Syllable]) -> list[Syllable] | None:
            if index == len(selected):
                form = Form(symbol for syllable in syllables for symbol in syllable.phonemes)
                return syllables if form not in (excluded or set()) and not self.check(form) else None
            structure, position_indexes = selected[index]
            positions = structure.positions
            classes = [positions[i].phoneme_class for i in position_indexes]
            if any(phoneme_class is None for phoneme_class in classes):
                return None
            symbols = [phoneme_class.symbols for phoneme_class in classes if phoneme_class is not None]
            if any(not choices for choices in symbols):
                return None
            chosen: list[str] = []

            def fill_position(position: int) -> list[Syllable] | None:
                if position == len(symbols):
                    parts = [positions[i].part for i in position_indexes]
                    if any(part is None for part in parts):
                        return None
                    syllable = Syllable(tuple(chosen), structure, tuple(position_indexes),
                                        tuple(part for part in parts if part is not None))
                    if any(
                        constraint.mode is ConstraintMode.BAN and constraint.matches(syllables + [syllable])
                        for constraint in self._constraints
                    ):
                        return None
                    return fill_phonemes(index + 1, syllables + [syllable])
                options = list(symbols[position])
                options.sort(key=lambda symbol: -math.log(max(rng.random(), 1e-12)) / weights[symbol])
                for symbol in options:
                    chosen.append(symbol)
                    answer = fill_position(position + 1)
                    chosen.pop()
                    if answer is not None:
                        return answer
                return None

            return fill_position(0)

        return choose_variants(0)

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

    def _restore_constraint(self, id: int, atoms: tuple[ConstraintAtom, ...], part: SyllablePart | None,
                            position: SyllablePosition, across_boundaries: bool,
                            mode: ConstraintMode) -> PhonotacticConstraint:
        constraint = PhonotacticConstraint(id, self, atoms, part, position, across_boundaries, mode)
        self._constraints.append(constraint)
        return constraint

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

__all__ = ["CantSyllabify", "ConstraintAtom", "PhonotacticConstraint", "Phonotactics", "Position",
           "Syllable", "SyllablePart", "SyllablePosition", "SyllableStructure", "ConstraintMode", "Violation",
           "parse_notation", "write_notation", "write_syllables"]

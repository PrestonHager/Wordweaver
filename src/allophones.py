# allophones.py

from collections.abc import Callable, Iterator

from ipapy import UNICODE_TO_IPA, is_valid_ipa

from phoneme_classes import PhonemeClass, PhonemeClasses
from phonology import Phoneme, PhonemeInventory

class WordBoundary:
    """The edge of a word, written # in rules. There's only one, WORD_BOUNDARY."""

    def __repr__(self) -> str:
        return "WORD_BOUNDARY"

    def __str__(self) -> str:
        return "#"

WORD_BOUNDARY = WordBoundary()

# One side of a rule's context: a Phoneme, a Phoneme Class, a word boundary, or None for nothing in particular.
# Sound Changes will use the same shape later.
ContextSide = Phoneme | PhonemeClass | WordBoundary | None

def is_valid_allophone(allophone: str) -> bool:
    """Check that an Allophone is IPA with at least one sound in it, like [ɾ] or [tʰ].

    Unlike a Phoneme, it can carry diacritics and length marks.
    """
    if not allophone or any(c.isspace() for c in allophone) or not is_valid_ipa(allophone):
        return False
    return any(UNICODE_TO_IPA.get(c) is not None and (UNICODE_TO_IPA[c].is_consonant or UNICODE_TO_IPA[c].is_vowel) for c in allophone)

def describe_side(side: ContextSide) -> str:
    if isinstance(side, PhonemeClass):
        return side.name
    return "" if side is None else str(side)

class AllophoneRule:
    """Says a Phoneme is pronounced as an Allophone when it comes between the `before` and `after` contexts."""

    def __init__(self, id: int, rules: "AllophoneRules", phoneme: Phoneme, allophone: str, before: ContextSide, after: ContextSide):
        self._id = id
        self._rules = rules
        self._phoneme = phoneme
        self._allophone = allophone
        self._before = before
        self._after = after

    @property
    def id(self) -> int:
        return self._id

    @property
    def phoneme(self) -> Phoneme:
        return self._phoneme

    @phoneme.setter
    def phoneme(self, phoneme: Phoneme | str):
        self._phoneme = self._rules._check_phoneme(phoneme)

    @property
    def allophone(self) -> str:
        return self._allophone

    @allophone.setter
    def allophone(self, allophone: str):
        self._allophone = self._rules._check_allophone(allophone)

    @property
    def before(self) -> ContextSide:
        return self._before

    @before.setter
    def before(self, side: ContextSide | str):
        self._before = self._rules._check_side(side)

    @property
    def after(self) -> ContextSide:
        return self._after

    @after.setter
    def after(self, side: ContextSide | str):
        self._after = self._rules._check_side(side)

    def edit(self, phoneme: Phoneme | str, allophone: str, before: ContextSide | str, after: ContextSide | str):
        """Change the whole rule at once. Everything is checked first, so a bad value leaves the rule as it was.

        :raises ValueError: If a Phoneme or Class isn't in this Language, or the Allophone isn't valid IPA.
        """
        checked = (self._rules._check_phoneme(phoneme), self._rules._check_allophone(allophone),
                   self._rules._check_side(before), self._rules._check_side(after))
        self._phoneme, self._allophone, self._before, self._after = checked

    def __str__(self) -> str:
        # Write it the usual way, like /t/ → [ɾ] / Vowel _ Vowel.
        text = f"/{self.phoneme}/ → [{self.allophone}]"
        if self.before is not None or self.after is not None:
            text += " / " + " ".join(s for s in (describe_side(self.before), "_", describe_side(self.after)) if s)
        return text

    def __repr__(self) -> str:
        return f"<AllophoneRule {self.id} {self}>"

class AllophoneRules:
    """All the Allophone Rules in one Language, in the order they were added."""

    def __init__(self, inventory: PhonemeInventory, classes: PhonemeClasses, new_id: Callable[[], int]):
        self._inventory = inventory
        self._classes = classes
        self._new_id = new_id
        self._rules: list[AllophoneRule] = []

    def add(self, phoneme: Phoneme | str, allophone: str, before: ContextSide | str=None, after: ContextSide | str=None) -> AllophoneRule:
        """Add a rule. Phonemes can be given as their IPA symbols.

        :raises ValueError: If a Phoneme or Class isn't in this Language, or the Allophone isn't valid IPA.
        """
        phoneme = self._check_phoneme(phoneme)
        allophone = self._check_allophone(allophone)
        before = self._check_side(before)
        after = self._check_side(after)
        return self._restore(self._new_id(), phoneme, allophone, before, after)

    def remove(self, rule: AllophoneRule):
        """Remove a rule.

        :raises ValueError: If the rule isn't in this Language.
        """
        self._rules.remove(rule)

    def of(self, symbol: str) -> list[str]:
        """Get a Phoneme's Allophones, each once, in rule order."""
        allophones = []
        for rule in self:
            if rule.phoneme.symbol == symbol and rule.allophone not in allophones:
                allophones.append(rule.allophone)
        return allophones

    def _restore(self, id: int, phoneme: Phoneme, allophone: str, before: ContextSide, after: ContextSide) -> AllophoneRule:
        rule = AllophoneRule(id, self, phoneme, allophone, before, after)
        self._rules.append(rule)
        return rule

    def _is_live(self, rule: AllophoneRule) -> bool:
        # A rule stops counting once its Phoneme, or anything in its context, is taken out of the Language.
        # It isn't saved after that, and putting a Phoneme back makes a new one, so the rule doesn't come back.
        return all(self._exists(part) for part in (rule.phoneme, rule.before, rule.after))

    def _exists(self, part) -> bool:
        if isinstance(part, Phoneme):
            return self._inventory.get(part.symbol) == part
        if isinstance(part, PhonemeClass):
            return any(c is part for c in self._classes)
        return True

    def _check_phoneme(self, phoneme: Phoneme | str) -> Phoneme:
        symbol = phoneme.symbol if isinstance(phoneme, Phoneme) else phoneme
        found = self._inventory.get(symbol)
        if found is None or (isinstance(phoneme, Phoneme) and found != phoneme):
            raise ValueError(f"/{symbol}/ isn't in this Language's Phoneme Inventory")
        return found

    def _check_allophone(self, allophone: str) -> str:
        if not is_valid_allophone(allophone):
            raise ValueError(f"[{allophone}] isn't a valid IPA Allophone")
        return allophone

    def _check_side(self, side: ContextSide | str) -> ContextSide:
        if side is None or isinstance(side, WordBoundary):
            return side
        if isinstance(side, PhonemeClass):
            if not any(c is side for c in self._classes):
                raise ValueError(f"The Phoneme Class {side.name} isn't in this Language")
            return side
        return self._check_phoneme(side)

    def __iter__(self) -> Iterator[AllophoneRule]:
        return iter([rule for rule in self._rules if self._is_live(rule)])

__all__ = ["WORD_BOUNDARY", "AllophoneRule", "AllophoneRules", "ContextSide", "is_valid_allophone"]

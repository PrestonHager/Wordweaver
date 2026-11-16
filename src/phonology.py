# phonology.py

from collections.abc import Callable, Iterator
from dataclasses import dataclass

from ipapy import UNICODE_TO_IPA
from ipapy.ipachar import IPAChar, IPAConsonant, IPAVowel

@dataclass(frozen=True)
class Phoneme:
    """A single distinctive sound of a Language, written as an IPA symbol, with a stable ID."""
    id: int
    symbol: str

    @property
    def ipa(self) -> IPAChar:
        return UNICODE_TO_IPA[self.symbol]

    def __str__(self) -> str:
        return self.symbol

def is_valid_phoneme(symbol: str) -> bool:
    """Check that a symbol is one IPA consonant or vowel."""
    return isinstance(UNICODE_TO_IPA.get(symbol), (IPAConsonant, IPAVowel))

class PhonemeInventory:
    """The set of Phonemes a Language uses, kept in the order they were added."""

    def __init__(self, new_id: Callable[[], int]):
        self._new_id = new_id
        self._phonemes: dict[str, Phoneme] = {}
        self._frequencies: dict[int, float] = {}

    def add(self, symbol: str) -> Phoneme:
        if symbol in self._phonemes:
            return self._phonemes[symbol]
        if not is_valid_phoneme(symbol):
            raise ValueError(f"Not an IPA consonant or vowel: {symbol!r}")
        phoneme = Phoneme(self._new_id(), symbol)
        self._phonemes[symbol] = phoneme
        return phoneme

    def remove(self, symbol: str):
        phoneme = self._phonemes.pop(symbol)
        self._frequencies.pop(phoneme.id, None)

    def set_symbols(self, symbols: list[str]):
        invalid = [s for s in symbols if not is_valid_phoneme(s)]
        if invalid:
            raise ValueError(f"Not IPA consonants or vowels: {', '.join(repr(s) for s in invalid)}")
        for symbol in [s for s in self._phonemes if s not in symbols]:
            self.remove(symbol)
        for symbol in symbols:
            self.add(symbol)

    def get(self, symbol: str) -> Phoneme | None:
        return self._phonemes.get(symbol)

    def frequency(self, symbol: str) -> float | None:
        return self._frequencies.get(self._phonemes[symbol].id)

    def set_frequency(self, symbol: str, frequency: float | None):
        phoneme = self._phonemes[symbol]
        if frequency is None:
            self._frequencies.pop(phoneme.id, None)
            return
        frequency = float(frequency)
        if not 0 < frequency < float("inf"):
            raise ValueError(f"A Phoneme Frequency has to be a positive number, not {frequency}")
        self._frequencies[phoneme.id] = frequency

    def weights(self) -> dict[str, float]:
        return {p.symbol: self._frequencies.get(p.id, 1.0) for p in self._phonemes.values()}

    @property
    def symbols(self) -> list[str]:
        return list(self._phonemes)

    def _restore(self, phoneme: Phoneme):
        self._phonemes[phoneme.symbol] = phoneme

    def __iter__(self) -> Iterator[Phoneme]:
        return iter(list(self._phonemes.values()))

    def __len__(self) -> int:
        return len(self._phonemes)

    def __contains__(self, symbol: str) -> bool:
        return symbol in self._phonemes

__all__ = ["Phoneme", "PhonemeInventory", "is_valid_phoneme"]

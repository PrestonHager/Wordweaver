# suprasegmentals.py

class Suprasegmentals:
    """A Language's Suprasegmental settings: whether it uses Stress and Length, and its tones.

    These are Language-wide for now. Putting them on syllables comes with Phonotactics.
    """

    def __init__(self, stress: bool=False, tones: list[str]=(), length: bool=False):
        self.stress = stress
        self.length = length
        self._tones: list[str] = []
        self.tones = list(tones)

    @property
    def tones(self) -> list[str]:
        """The Language's tones, like ["high", "low"] or ["˥", "˩"]. Empty means it doesn't use Tone."""
        return list(self._tones)

    @tones.setter
    def tones(self, tones: list[str]):
        """
        :raises ValueError: If a tone is blank or listed twice. The tones aren't changed then.
        """
        tones = [tone.strip() for tone in tones]
        if any(not tone for tone in tones):
            raise ValueError("A tone needs a name")
        if len(set(tones)) != len(tones):
            raise ValueError("Each tone can only be listed once")
        self._tones = tones

    @property
    def uses_tone(self) -> bool:
        return bool(self._tones)

    def __repr__(self) -> str:
        return f"<Suprasegmentals stress={self.stress} tones={self._tones} length={self.length}>"

__all__ = ["Suprasegmentals"]

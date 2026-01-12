# phonology.py

import random
from enum import Enum

from ipapy import IPA_TO_UNICODE
from ipapy.ipachar import IPAChar


# Declare the Phonemes class to include current IPA characters
def define_phoneme_types():
    from ipapy import IPA_CHARS
    consonants = []
    vowels = []
    for char in IPA_CHARS:
        if char.is_consonant:
            consonants.append(char)
        elif char.is_vowel:
            vowels.append(char)
    return {"CONSONANT": consonants, "VOWEL": vowels}


# Call the function to define the enum
Phonemes = Enum("Phonemes", define_phoneme_types())


class PhonemeConstraint:
    def __init__(self, phoneme: Phonemes, optional: bool = False):
        self.phoneme = phoneme
        self.optional = optional

    def __repr__(self) -> str:
        return f"<{self.__class__.__module__}.{self.__class__.__qualname__} \
of type {self.phoneme} - optional: {self.optional}>"


class PhonemeGenerator:
    def __init__(self, inventory: list[IPAChar] | dict[Phonemes, list[IPAChar]],
                 constraint: tuple[PhonemeConstraint] = (PhonemeConstraint(Phonemes.VOWEL),),
                 *secondary_constraints: tuple[PhonemeConstraint]):
        """
        Initialize the PhonemeGenerator class with an inventory of IPAChar objects and specified constraint(s).

        :param inventory: list[IPAChar] | dict[Phonemes, list[IPAChar]]: A list or dictionary of IPAChar objects.
        :param constraint: tuple[PhonemeConstraint]: A tuple of PhonemeConstraint objects.
        :param *secondary_constraints: tuple[PhonemeConstraint]: A tuple of PhonemeConstraint objects.
        """
        # Check all types
        if not isinstance(inventory, dict) and not isinstance(inventory, list):
            raise TypeError("Inventory must be a list or dict.")
        if not isinstance(constraint, tuple):
            raise TypeError("Constraint must be a tuple.")
        if len(secondary_constraints) > 0 and all(not isinstance(i, tuple) for i in secondary_constraints):
            raise TypeError("Secondary constraints must be a tuple.")
        # Assign values
        self.constraint = constraint
        self.secondary_constraints = list(secondary_constraints)
        self._inventory = self._sort_inventory(inventory)
        # Ensure all phoneme constraint types are defined in the inventory
        for t in [i.phoneme for p in self.secondary_constraints + [self.constraint] for i in p]:
            # Check if the phoneme type is defined in the inventory
            if self._inventory[t] == []:
                raise ValueError(f"Phonemes of type {t} are not defined in the inventory.")

    @property
    def inventory(self):
        return self._inventory

    @inventory.setter
    def inventory(self, inventory: list[IPAChar] | list[str]):
        self._inventory = self._sort_inventory(inventory)

    def _sort_inventory(self, inventory: list[IPAChar] | dict[Phonemes, list[IPAChar]]) -> dict[Phonemes, list[IPAChar]]:
        if isinstance(inventory, dict):
            return inventory
        else:
            inv = {t: [] for t in Phonemes}
            # Loop through each phoneme in the inventory
            # and assign it to the appropriate enum member
            for phoneme in inventory:
                # if the phoneme doesn't have a unicode representation
                # then create one now
                if phoneme.unicode_repr is None:
                    try:
                        phoneme.unicode_repr = IPA_TO_UNICODE[phoneme.canonical_representation]
                    except KeyError:
                        raise ValueError(
                            f"Phoneme {phoneme} does not have a unicode",
                            "representation; probably because it doesn't exist."
                        )
                for phoneme_name in Phonemes._member_names_:
                    t = Phonemes[phoneme_name]
                    # loop through the enum members to find a match
                    for char in t.value:
                        if char.is_equivalent(phoneme):
                            inv[t].append(phoneme)
            return inv

    def constrain(self, constraint: tuple[PhonemeConstraint], *secondary_constraints: tuple[tuple[PhonemeConstraint]]):
        """Set the constraint(s) for the PhonemeGenerator object.

        Arguments:
            constraint: tuple: A tuple of PhonemeConstraint objects.
            *secondary_constraints: tuple: A tuple of PhonemeConstraint objects.

        Returns:
            PhonemeGenerator: The PhonemeGenerator object.
        """
        self.constraint = constraint
        if len(secondary_constraints) > 0:
            self.secondary_constraints = secondary_constraints
        return self

    def generate_syllables(self, n: int):
        """Generate a list of syllables based on the constraints set for the PhonemeGenerator object.

        The first syllable of each generated word will use the first constraint,
        the second syllable will use the second constraint, and so on.
        If there are more syllables than constraints, the last constraint will
        be used for the remaining syllables.

        Arguments:
            n: int: The number of syllables to generate.

        Yeilds:
            syllable: list[IPAChar]: A list of IPAChar objects representing a syllable.

        Raises:
            ValueError: If the phoneme type is not defined in the inventory.
        """
        for i in range(n):
            syllable = []
            if i == 0 or len(self.secondary_constraints) == 0:
                constraint = self.constraint
            elif i < len(self.secondary_constraints):
                constraint = self.secondary_constraints[i]
            else:
                constraint = self.secondary_constraints[-1]
            for cons in constraint:
                if (cons.optional and random.random() < 0.5) or not cons.optional:
                    # optional phoneme so we generate it half the time
                    syllable.append(random.choice(self._inventory[cons.phoneme]))
            yield syllable

    def generate_random(self, syllable_length: int, n: int) -> list[list[IPAChar]]:
        return [
            [j for j in self.generate_syllables(syllable_length)] for i in range(n)
        ]

    def print_word(self, syllable_list: list[IPAChar], seperator: str = ''):
        print(seperator.join([''.join([j.unicode_repr for j in i]) for i in syllable_list]))


__all__ = ["Phonemes", "PhonemeConstraint", "PhonemeGenerator"]

if __name__ == "__main__":
    inventory = [
        IPAChar(descriptors="open front unrounded vowel"),
        IPAChar(descriptors="close front unrounded vowel"),
        IPAChar(descriptors="voiceless bilabial plosive consonant"),
        IPAChar(descriptors="voiceless alveolar plosive consonant"),
        IPAChar(descriptors="voiceless labiodental non-sibilant-fricative consonant"),
        IPAChar(descriptors="voiceless bilabial non-sibilant-fricative consonant"),
    ]
    gen = PhonemeGenerator(inventory)
    gen.constrain((PhonemeConstraint(Phonemes.CONSONANT, optional=True),
                   PhonemeConstraint(Phonemes.VOWEL),),
                  (PhonemeConstraint(Phonemes.CONSONANT, optional=False),
                   PhonemeConstraint(Phonemes.VOWEL),
                   PhonemeConstraint(Phonemes.CONSONANT, optional=True),))
    random_words = gen.generate_random(3, 5)
    for word in random_words:
        gen.print_word(word)

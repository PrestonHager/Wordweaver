# phonology.py

import random
from enum import Enum

from phonology_const import *

# Helper function for the _const file.
# def generate_phoneme_tables(table):
#     phonemes = {}
#     key_list = {}
#     for t in table.keys():
#         for l in table[t].keys():
#             for value, key in table[t][l].items():
#                 phonemes[key] = f"{t}/{l}"
#                 key_list[value] = key
#     return (phonemes, key_list)

class PhonemeType(Enum):
    CONSONANT = 1
    PULMONIC_CONSONANT = 2
    NON_PULMONIC_CONSONANT = 3
    VOWEL = 10

# Necessary for the Phoneme class
# because we access the class in a method in a circular way
class PhonemeConstraint:
    pass

class Phoneme:
    def __init__(self, sound: str=None, stype: str=None):
        self.sound_ascii = sound
        self.stype = stype
        self.sound = self._lookup(sound)
    
    def __str__(self) -> str:
        return f"{self.sound}"

    def __repr__(self) -> str:
        # return f"<{self.__class__.__module__}.{self.__class__.__qualname__} of type {self.stype} - {self.sound}>"
        return f"'{self.sound_ascii}'"

    def __eq__(self, other) -> bool:
        return self.sound == other.sound and self.stype == other.stype
    
    def _lookup(self, sound: str) -> str:
        if self.stype == PhonemeType.PULMONIC_CONSONANT:
            return PULMONIC_CONSONANTS_LOOKUP[sound]
        elif self.stype == PhonemeType.VOWEL:
            return VOWELS_LOOKUP[sound]
    
    def constraint(self, optional: bool=False) -> PhonemeConstraint:
        return PhonemeConstraint(self, optional)
    
    def encode(self):
        return self.sound.encode()

class PhonemeConstraint:
    def __init__(self, phoneme: Phoneme, optional: bool=False):
        self.phoneme = phoneme
        self.optional = optional

class PhonemeGenerator:
    def __init__(self, inventory, constraint: tuple[PhonemeConstraint]=(PhonemeConstraint(PhonemeType.VOWEL),), secondary_constraints=[]):
        self.inventory = self._sort_inventory(inventory)
        self.constraint = constraint
        self.secondary_constraints = secondary_constraints
    
    def _sort_inventory(self, inventory) -> dict[PhonemeType, list[Phoneme]]:
        if type(inventory) == dict:
            return inventory
        else:
            inv = {t: [] for t in PhonemeType}
            for phoneme in inventory:
                if phoneme.stype == PhonemeType.CONSONANT or phoneme.stype == PhonemeType.PULMONIC_CONSONANT:
                    inv[PhonemeType.CONSONANT].append(phoneme)
                elif phoneme.stype == PhonemeType.VOWEL:
                    inv[PhonemeType.VOWEL].append(phoneme)
            return inv
    
    def constrain(self, constraint: tuple[PhonemeConstraint], *args):
        self.constraint = constraint
        if len(args) > 0:
            self.secondary_constraints = args
        return self
    
    def _generate_syllables(self, n: int):
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
                    syllable.append(random.choice(self.inventory[cons.phoneme]))
            yield syllable
    
    def generate_random(self, syllable_length: int, n: int) -> list[list[Phoneme]]:
        return [
            [j for j in self._generate_syllables(syllable_length)] for i in range(n)
        ]
    
    def print_word(self, syllable_list: list[Phoneme], seperator: str=''):
        print(seperator.join([''.join([j.sound for j in i]) for i in syllable_list]))

__all__ = ["Phoneme", "PhonemeType", "PhonemeConstraint", "PhonemeGenerator"]

if __name__ == "__main__":
    inventory = [
        Phoneme("a", PhonemeType.VOWEL),
        Phoneme("i", PhonemeType.VOWEL),
        Phoneme("f", PhonemeType.PULMONIC_CONSONANT),
        Phoneme("p", PhonemeType.PULMONIC_CONSONANT),
        Phoneme("t", PhonemeType.PULMONIC_CONSONANT)
    ]
    gen = PhonemeGenerator(inventory)
    gen.constrain((PhonemeConstraint(PhonemeType.CONSONANT, optional=True),
                   PhonemeConstraint(PhonemeType.VOWEL),),
                  (PhonemeConstraint(PhonemeType.CONSONANT, optional=False),
                   PhonemeConstraint(PhonemeType.VOWEL),
                   PhonemeConstraint(PhonemeType.CONSONANT, optional=True),))
    random_words = gen.generate_random(3, 5)
    for word in random_words:
        gen.print_word(word)


# test/test_phonology.py

import unittest

# Add the parent directory to the path so we can import the module we want to test
import sys
from os import path
sys.path.append(path.abspath(path.join(path.dirname(__file__), '../src')))

from phonology import Phonemes, PhonemeConstraint, PhonemeGenerator

from ipapy.ipachar import IPAChar

INVENTORY = [
    IPAChar("plosive bilabial voiced consonant"),
    IPAChar("plosive alveolar voiced consonant"),
    IPAChar("plosive retroflex voiceless consonant"),
    IPAChar("open front unrounded vowel"),
    IPAChar("close front unrounded vowel"),
]

INVENTORY_DICT = {
    Phonemes.CONSONANT: [
        IPAChar("plosive bilabial voiced consonant"),
        IPAChar("plosive alveolar voiced consonant"),
        IPAChar("plosive retroflex voiceless consonant"),
    ],
    Phonemes.VOWEL: [
        IPAChar("open front unrounded vowel"),
        IPAChar("close front unrounded vowel"),
    ],
}

CONSTRAINTS = (
    PhonemeConstraint(Phonemes.CONSONANT),
    PhonemeConstraint(Phonemes.VOWEL),
)

SECONDARY_CONSTRAINTS = (
    PhonemeConstraint(Phonemes.CONSONANT, optional=False),
    PhonemeConstraint(Phonemes.VOWEL),
    PhonemeConstraint(Phonemes.CONSONANT, optional=True),
)

class TestPhonemeGenerator(unittest.TestCase):
    def test_init(self):
        # Test the init method
        phoneme_generator = PhonemeGenerator(INVENTORY, CONSTRAINTS, SECONDARY_CONSTRAINTS)
        # NOTE: The str() function is used to compare the dictionaries because the IPAChar objects are not hashable
        self.assertEqual(phoneme_generator.inventory, INVENTORY_DICT)
        self.assertEqual(phoneme_generator.constraint, CONSTRAINTS)
        self.assertEqual(phoneme_generator.secondary_constraints, [SECONDARY_CONSTRAINTS])
    
    def test_init_invalid(self):
        # Test the init method with invalid arguments
        with self.assertRaises(ValueError):
            phoneme_generator = PhonemeGenerator([IPAChar("invalid phoneme")], (), ())
        with self.assertRaises(ValueError):
            phoneme_generator = PhonemeGenerator([], (PhonemeConstraint(Phonemes.VOWEL),), ())
        with self.assertRaises(ValueError):
            phoneme_generator = PhonemeGenerator([], (), (PhonemeConstraint(Phonemes.VOWEL),))
    
    def test_generate_syllables(self):
        # Test the generate_syllables method
        phoneme_generator = PhonemeGenerator(INVENTORY, CONSTRAINTS, SECONDARY_CONSTRAINTS)
        syllables = list(phoneme_generator.generate_syllables(7))
        self.assertEqual(len(syllables), 7)
        for syllable in syllables:
            # Note that range is exclusive of the stop value
            # so this produces a range of 2 to 3 inclusive
            self.assertIn(len(syllable), range(2, 4))

if __name__ == "__main__":
    unittest.main()
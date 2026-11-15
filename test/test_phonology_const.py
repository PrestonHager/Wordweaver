# test/test_phonology_const.py

import unittest

# Add the parent directory to the path so we can import the module we want to test
import sys
from os import path
sys.path.append(path.abspath(path.join(path.dirname(__file__), '../src')))

from ipapy import UNICODE_TO_IPA

from phonology_const import PULMONIC_CONSONANTS, NON_PULMONIC_CONSONANTS, VOWELS

# Our chart keys don't always match the names ipapy uses, so map them here.
CHART_TO_IPAPY = {
    "bi-labial": {"bilabial"},
    "tap": {"flap"},
    "fricative": {"sibilant-fricative", "non-sibilant-fricative"},
    "post-alveolar": {"post-alveolar", "palato-alveolar"},
    "palato-alveolar": {"palatal"},
    "front": {"front", "near-front"},
    "back": {"back", "near-back"},
}

def ipapy_names(key):
    return CHART_TO_IPAPY.get(key, {key})

class TestPhonologyConst(unittest.TestCase):
    def assert_descriptors(self, symbol, *keys):
        char = UNICODE_TO_IPA.get(symbol)
        self.assertIsNotNone(char, f"ipapy doesn't know {symbol!r}")
        for key in keys:
            self.assertTrue(ipapy_names(key) & set(char.descriptors),
                            f"{symbol!r} should be {key}, ipapy says {char.descriptors}")

    def test_spot_check_plosives(self):
        plosives = PULMONIC_CONSONANTS["plosive"]
        self.assertEqual(plosives["bi-labial"]["voiceless"], "p")
        self.assertEqual(plosives["bi-labial"]["voiced"], "b")
        self.assertEqual(plosives["alveolar"]["voiceless"], "t")
        self.assertEqual(plosives["alveolar"]["voiced"], "d")

    def test_consonants_match_ipa(self):
        # Check every consonant cell's manner, place and voicing against ipapy.
        for chart in (PULMONIC_CONSONANTS, NON_PULMONIC_CONSONANTS):
            for manner, places in chart.items():
                for place, voicings in places.items():
                    for voicing, symbol in voicings.items():
                        with self.subTest(symbol=symbol):
                            self.assert_descriptors(symbol, manner, place, voicing)

    def test_vowels_match_ipa(self):
        # Same as above but height, backness and rounding for the vowels.
        for height, places in VOWELS.items():
            for place, roundings in places.items():
                for rounding, symbol in roundings.items():
                    with self.subTest(symbol=symbol):
                        self.assert_descriptors(symbol, height, place, rounding)

if __name__ == "__main__":
    unittest.main()

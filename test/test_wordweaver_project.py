# test/wordweaver_project.py

import unittest

# Add the parent directory to the path so we can import the module we want to test
import sys
from os import path
sys.path.append(path.abspath(path.join(path.dirname(__file__), '../src')))

from ipapy.ipachar import IPAChar

from wordweaver_project import WordweaverProject

PULMONIC_INVENTORY_STR = [
    "p",
    "d",
    "n",
]
PULMONIC_INVENTORY = [
    IPAChar("bilabial consonant plosive voiceless"),
    IPAChar("consonant plosive alveolar voiced"),
    IPAChar("consonant alveolar nasal voiced"),
]
NON_PULMONIC_INVENTORY_STR = [
    "ǀ",
]
NON_PULMONIC_INVENTORY = [
    IPAChar("click consonant dental voiceless"),
]
VOWEL_INVENTORY_STR = [
    "a",
    "i",
    "ə",
    "u",
    "ɯ",
]
VOWEL_INVENTORY = [
    IPAChar("front open unrounded vowel"),
    IPAChar("close front unrounded vowel"),
    IPAChar("mid central unrounded vowel"),
    IPAChar("back close rounded vowel"),
    IPAChar("back close unrounded vowel"),
]
LEXICON = {}

class TestWordweaverProject(unittest.TestCase):
    def test_init(self):
        # Test the init method
        project = WordweaverProject('Test Project',
                                    pulmonic_inventory=PULMONIC_INVENTORY, non_pulmonic_inventory=NON_PULMONIC_INVENTORY, vowel_inventory=VOWEL_INVENTORY,
                                    lexicon=LEXICON)
        self.assertEqual(project.name, 'Test Project')
        self.assertEqual(project.pulmonic_inventory, PULMONIC_INVENTORY)
        self.assertEqual(project.non_pulmonic_inventory, NON_PULMONIC_INVENTORY)
        self.assertEqual(project.vowel_inventory, VOWEL_INVENTORY)
        self.assertEqual(project.lexicon, LEXICON)
    
    def test_init_convert(self):
        # Test the init method with string phonemes
        project = WordweaverProject('Test Project',
                                    pulmonic_inventory=PULMONIC_INVENTORY_STR,
                                    non_pulmonic_inventory=NON_PULMONIC_INVENTORY_STR,
                                    vowel_inventory=VOWEL_INVENTORY_STR,
                                    lexicon=LEXICON)
        self.assertEqual(project.name, 'Test Project')
        self.assertEqual(project.pulmonic_inventory, PULMONIC_INVENTORY)
        self.assertEqual(project.non_pulmonic_inventory, NON_PULMONIC_INVENTORY)
        self.assertEqual(project.vowel_inventory, VOWEL_INVENTORY)
        self.assertEqual(project.lexicon, LEXICON)

    def test_init_invalid(self):
        # Test the init method with invalid phonemes
        with self.assertRaises(ValueError):
            WordweaverProject('Test Project',
                            pulmonic_inventory=["plosive bilabial voiceless consonant", IPAChar("nasal dental voiceless consonant")],
                            non_pulmonic_inventory=[],
                            vowel_inventory=[],
                            lexicon={})
    
    def test_init_invalid2(self):
        # Test the init method with invalid phonemes
        with self.assertRaises(ValueError):
            WordweaverProject('Test Project',
                            pulmonic_inventory=[],
                            non_pulmonic_inventory=[],
                            vowel_inventory=["open front unrounded vowel", IPAChar("back close rounded vowel")],
                            lexicon={})
    
    # TODO: add tests for
    # - Maximum name length
    # - Maximum inventory length
    # - Maximum lexicon length
    # - Invalid phonemes and phoneme types
    # - Invalid project names

    def test_save(self):
        # Test the save method
        project = WordweaverProject('Test Project',
                                    file='test_project.wwproj', pulmonic_inventory=PULMONIC_INVENTORY, non_pulmonic_inventory=NON_PULMONIC_INVENTORY, vowel_inventory=VOWEL_INVENTORY,
                                    lexicon=LEXICON)
        project.save()
        with open('test_project.wwproj', 'rb') as f:
            data = f.read()
        self.assertEqual(data, b"\x87\xaf\xfa\x87\x01"\
                         b"\x00\x0cTest Project"\
                         b"\x03\x01p\x01d\x01n"\
                         b"\x01\x02\xc7\x80"\
                         b"\x05\x01a\x01i\x02\xc9\x99\x01u\x02\xc9\xaf"\
                         b"\x00"\
                         b"\x00\x00")
    
    def test_from_file(self):
        project = WordweaverProject('Test Project',
                                    file='test_project.wwproj', pulmonic_inventory=PULMONIC_INVENTORY, non_pulmonic_inventory=NON_PULMONIC_INVENTORY, vowel_inventory=VOWEL_INVENTORY,
                                    lexicon=LEXICON)
        project.save()
        # Test the open file method
        project = WordweaverProject.from_file('test_project.wwproj')
        self.assertEqual(project.name, 'Test Project')
        self.assertEqual(str(project.pulmonic_inventory), str(PULMONIC_INVENTORY))
        self.assertEqual(str(project.non_pulmonic_inventory), str(NON_PULMONIC_INVENTORY))
        self.assertEqual(str(project.vowel_inventory), str(VOWEL_INVENTORY))
        self.assertEqual(project.lexicon, LEXICON)

if __name__ == "__main__":
    unittest.main()
# test/wordweaver_project.py

import unittest

# Add the parent directory to the path so we can import the module we want to test
import sys
from os import path
sys.path.append(path.abspath(path.join(path.dirname(__file__), '..')))

from wordweaver_project import WordweaverProject
from phonology import Phoneme, PhonemeType

PULMONIC_INVENTORY = [
    Phoneme('p', PhonemeType.PULMONIC_CONSONANT),
    Phoneme('gh', PhonemeType.PULMONIC_CONSONANT),
    Phoneme('ng', PhonemeType.PULMONIC_CONSONANT)
]
NON_PULMONIC_INVENTORY = []
VOWEL_INVENTORY = [
    Phoneme('a', PhonemeType.VOWEL),
    Phoneme('eu', PhonemeType.VOWEL),
    Phoneme('i', PhonemeType.VOWEL),
    Phoneme('uh', PhonemeType.VOWEL),
    Phoneme('uv', PhonemeType.VOWEL)
]
LEXICON = []

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
                                    pulmonic_inventory=['p', 'gh', 'ng'],
                                    non_pulmonic_inventory=[],
                                    vowel_inventory=['a', 'eu', 'i', 'uh', 'uv'],
                                    lexicon=[])
        self.assertEqual(project.name, 'Test Project')
        self.assertEqual(project.pulmonic_inventory, PULMONIC_INVENTORY)
        self.assertEqual(project.non_pulmonic_inventory, NON_PULMONIC_INVENTORY)
        self.assertEqual(project.vowel_inventory, VOWEL_INVENTORY)
        self.assertEqual(project.lexicon, LEXICON)

    def test_init_invalid(self):
        # Test the init method with invalid phonemes
        with self.assertRaises(ValueError):
            WordweaverProject('Test Project',
                            pulmonic_inventory=['p', 'gh', 'ng', Phoneme('l', PhonemeType.PULMONIC_CONSONANT)],
                            non_pulmonic_inventory=[],
                            vowel_inventory=['a', 'eu', 'i', 'uh', 'uv'],
                            lexicon=[])
    
    def test_init_invalid2(self):
        # Test the init method with invalid phonemes
        with self.assertRaises(ValueError):
            WordweaverProject('Test Project',
                            pulmonic_inventory=['p', 'gh', 'ng'],
                            non_pulmonic_inventory=[],
                            vowel_inventory=['a', 'eu', 'i', 'uh', Phoneme('uv', PhonemeType.VOWEL)],
                            lexicon=[])
    
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
                         b"\x03\x00\x00\x00p\x00\x00\xCA\x94\x00\x00\xC5\x8B"\
                         b"\x00"\
                         b"\x05\x00\x00\x00a\x00\x00\xC9\x98\x00\x00\x00i\x00\x00\xCA\x8C\x00\x00\xC9\xAF"\
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
        self.assertEqual(project.pulmonic_inventory, PULMONIC_INVENTORY)
        self.assertEqual(project.non_pulmonic_inventory, NON_PULMONIC_INVENTORY)
        self.assertEqual(project.vowel_inventory, VOWEL_INVENTORY)
        self.assertEqual(project.lexicon, LEXICON)

if __name__ == "__main__":
    unittest.main()
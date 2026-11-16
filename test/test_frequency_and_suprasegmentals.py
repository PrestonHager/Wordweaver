# test/test_frequency_and_suprasegmentals.py

import tempfile
import unittest

# Add the parent directory to the path so we can import the module we want to test
import sys
from os import path
sys.path.append(path.abspath(path.join(path.dirname(__file__), '../src')))

from wordweaver_project import Project

class TestFrequencyAndSuprasegmentals(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file = path.join(self.temp_dir.name, "test.wwproj")
        self.project = Project("Test Project")
        self.language = self.project.add_language("Test")
        self.language.inventory.set_symbols(["p", "t", "k", "a", "i"])

    def tearDown(self):
        self.temp_dir.cleanup()

    def round_trip(self):
        self.project.save(self.file)
        return Project.load(self.file).languages[0]

    def test_defaults(self):
        inventory = self.language.inventory
        self.assertIsNone(inventory.frequency("p"))
        # With no Frequencies, every Phoneme counts the same.
        self.assertEqual(inventory.weights(), {"p": 1.0, "t": 1.0, "k": 1.0, "a": 1.0, "i": 1.0})
        suprasegmentals = self.language.suprasegmentals
        self.assertFalse(suprasegmentals.stress)
        self.assertEqual(suprasegmentals.tones, [])
        self.assertFalse(suprasegmentals.uses_tone)
        self.assertFalse(suprasegmentals.length)
        loaded = self.round_trip()
        self.assertIsNone(loaded.inventory.frequency("p"))
        self.assertEqual(loaded.suprasegmentals.tones, [])
        self.assertFalse(loaded.suprasegmentals.stress)

    def test_frequency_round_trip(self):
        inventory = self.language.inventory
        inventory.set_frequency("a", 5)
        inventory.set_frequency("t", 2.5)
        self.assertEqual(inventory.frequency("a"), 5.0)
        self.assertEqual(inventory.weights(), {"p": 1.0, "t": 2.5, "k": 1.0, "a": 5.0, "i": 1.0})
        loaded = self.round_trip().inventory
        self.assertEqual(loaded.frequency("a"), 5.0)
        self.assertEqual(loaded.frequency("t"), 2.5)
        self.assertIsNone(loaded.frequency("p"))
        self.assertEqual(loaded.weights(), inventory.weights())

    def test_clear_frequency(self):
        self.language.inventory.set_frequency("a", 3)
        self.language.inventory.set_frequency("a", None)
        self.assertIsNone(self.round_trip().inventory.frequency("a"))

    def test_invalid_frequency(self):
        inventory = self.language.inventory
        for bad in (0, -1, float("inf"), float("nan")):
            with self.assertRaises(ValueError, msg=repr(bad)):
                inventory.set_frequency("a", bad)
        with self.assertRaises(KeyError):
            inventory.set_frequency("ʃ", 2)
        self.assertIsNone(inventory.frequency("a"))

    def test_removed_phoneme_loses_its_frequency(self):
        inventory = self.language.inventory
        inventory.set_frequency("a", 4)
        inventory.remove("a")
        inventory.add("a")
        self.assertIsNone(inventory.frequency("a"))

    def test_frequency_keeps_allophone_rules(self):
        # Setting a Frequency mustn't swap out the Phoneme, or rules pointing at it would drop.
        self.language.add_allophone_rule("t", "ɾ", before="a", after="a")
        self.language.inventory.set_frequency("t", 3)
        self.language.inventory.set_frequency("a", 2)
        self.assertEqual(self.language.allophones_of("t"), ["ɾ"])

    def test_suprasegmentals_round_trip(self):
        other = self.project.add_language("Other")
        self.language.suprasegmentals.stress = True
        self.language.suprasegmentals.tones = ["high", "mid", "low"]
        other.suprasegmentals.length = True
        loaded = self.round_trip()
        self.assertTrue(loaded.suprasegmentals.stress)
        self.assertEqual(loaded.suprasegmentals.tones, ["high", "mid", "low"])
        self.assertTrue(loaded.suprasegmentals.uses_tone)
        self.assertFalse(loaded.suprasegmentals.length)
        loaded_other = Project.load(self.file).languages[1]
        self.assertFalse(loaded_other.suprasegmentals.stress)
        self.assertEqual(loaded_other.suprasegmentals.tones, [])
        self.assertTrue(loaded_other.suprasegmentals.length)

    def test_invalid_tones(self):
        suprasegmentals = self.language.suprasegmentals
        suprasegmentals.tones = ["˥", "˩"]
        for bad in (["high", "high"], ["high", " "]):
            with self.assertRaises(ValueError):
                suprasegmentals.tones = bad
        self.assertEqual(suprasegmentals.tones, ["˥", "˩"])

    def test_round_trip_through_patches(self):
        self.language.inventory.set_frequency("a", 5)
        self.project.save(self.file)
        with open(self.file, "rb") as f_in:
            base = f_in.read()
        # Now change both, then save again as a patch.
        self.language.inventory.set_frequency("a", None)
        self.language.inventory.set_frequency("k", 0.5)
        self.language.suprasegmentals.stress = True
        self.language.suprasegmentals.tones = ["rising", "falling"]
        self.language.suprasegmentals.length = True
        self.project.save()
        with open(self.file, "rb") as f_in:
            self.assertTrue(f_in.read().startswith(base))
        loaded = Project.load(self.file).languages[0]
        self.assertIsNone(loaded.inventory.frequency("a"))
        self.assertEqual(loaded.inventory.frequency("k"), 0.5)
        self.assertTrue(loaded.suprasegmentals.stress)
        self.assertEqual(loaded.suprasegmentals.tones, ["rising", "falling"])
        self.assertTrue(loaded.suprasegmentals.length)

if __name__ == "__main__":
    unittest.main()

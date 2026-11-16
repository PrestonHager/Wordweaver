# test/test_phoneme_classes.py

import tempfile
import unittest

# Add the parent directory to the path so we can import the module we want to test
import sys
from os import path
sys.path.append(path.abspath(path.join(path.dirname(__file__), '../src')))

from wordweaver_project import Project

class TestPhonemeClasses(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file = path.join(self.temp_dir.name, "test.wwproj")
        self.project = Project("Test Project")
        self.language = self.project.add_language("Test")
        self.language.inventory.set_symbols(["m", "p", "b", "s", "t͡s", "l", "ǀ", "a", "i", "u"])

    def tearDown(self):
        self.temp_dir.cleanup()

    def round_trip(self):
        self.project.save(self.file)
        return Project.load(self.file).languages[0]

    def class_names(self, language, symbol):
        return {c.name for c in language.classes_of(symbol)}

    def test_defaults_come_from_ipa_features(self):
        self.assertTrue({"Consonant", "Nasal", "Voiced", "Labial", "Sonorant"} <= self.class_names(self.language, "m"))
        self.assertNotIn("Vowel", self.class_names(self.language, "m"))
        self.assertTrue({"Vowel", "Open", "Front", "Unrounded"} <= self.class_names(self.language, "a"))
        self.assertTrue({"Affricate", "Sibilant", "Voiceless", "Obstruent"} <= self.class_names(self.language, "t͡s"))
        self.assertIn("Click", self.class_names(self.language, "ǀ"))
        self.assertEqual(self.language.get_class("Nasal").symbols, ["m"])
        self.assertEqual(self.language.get_class("Vowel").symbols, ["a", "i", "u"])
        self.assertEqual(self.language.get_class("Stop").symbols, ["p", "b"])

    def test_user_classes_round_trip(self):
        liquids = self.language.add_class("Liquids")
        liquids.add("l")
        liquids.add("s")
        liquids.remove("s")
        empty = self.language.add_class("Empty")
        loaded = self.round_trip()
        self.assertEqual(loaded.get_class("Liquids").symbols, ["l"])
        self.assertEqual(loaded.get_class("Liquids").id, liquids.id)
        self.assertEqual(loaded.get_class("Empty").symbols, [])
        self.assertEqual(loaded.get_class("Empty").id, empty.id)
        self.assertIn("Liquids", self.class_names(loaded, "l"))

    def test_rename_and_delete_user_classes(self):
        kept = self.language.add_class("Old")
        kept.add("a")
        kept.name = "New"
        gone = self.language.add_class("Gone")
        self.language.remove_class(gone)
        loaded = self.round_trip()
        self.assertEqual(loaded.get_class("New").symbols, ["a"])
        self.assertIsNone(loaded.get_class("Old"))
        self.assertIsNone(loaded.get_class("Gone"))
        # The deleted Class's ID was the newest one, so a reused ID would show up right after loading.
        self.assertGreater(loaded.add_class("Third").id, gone.id)

    def test_class_ids_are_unique(self):
        other = self.project.add_language("Other")
        ids = [c.id for language in (self.language, other) for c in language.classes]
        ids += [self.language.add_class("Mine").id, other.add_class("Mine").id]
        ids += [language.id for language in self.project.languages]
        ids += [p.id for language in self.project.languages for p in language.inventory]
        self.assertEqual(len(ids), len(set(ids)))

    def test_default_class_ids_survive_save_and_load(self):
        ids = {c.name: c.id for c in self.language.classes}
        loaded = self.round_trip()
        self.assertEqual({c.name: c.id for c in loaded.classes}, ids)

    def test_class_needs_a_phoneme_from_the_inventory(self):
        liquids = self.language.add_class("Liquids")
        with self.assertRaises(KeyError):
            liquids.add("r")

    def test_removing_a_phoneme_takes_it_out_of_classes(self):
        liquids = self.language.add_class("Liquids")
        liquids.add("l")
        self.language.inventory.remove("l")
        self.assertEqual(liquids.symbols, [])
        # Adding it back makes a new Phoneme, which isn't in the hand-made Class.
        self.language.inventory.add("l")
        self.assertEqual(liquids.symbols, [])

    def test_new_phonemes_join_untouched_defaults_only(self):
        nasal = self.language.get_class("Nasal")
        stop = self.language.get_class("Stop")
        stop.remove("b")
        self.language.inventory.add("n")
        self.language.inventory.add("d")
        self.assertEqual(nasal.symbols, ["m", "n"])
        # Stop was edited by hand, so /d/ doesn't get put in it.
        self.assertEqual(stop.symbols, ["p"])
        self.assertIn("Voiced", self.class_names(self.language, "d"))
        self.assertNotIn("Stop", self.class_names(self.language, "d"))

    def test_hand_edits_to_defaults_round_trip(self):
        stop = self.language.get_class("Stop")
        stop.remove("b")
        stop.add("s")
        self.language.get_class("Vowel").name = "Vocoid"
        loaded = self.round_trip()
        self.assertEqual(loaded.get_class("Stop").symbols, ["p", "s"])
        self.assertEqual(loaded.get_class("Stop").id, stop.id)
        self.assertIsNone(loaded.get_class("Vowel"))
        self.assertEqual(loaded.get_class("Vocoid").symbols, ["a", "i", "u"])
        # After loading, the edited default still doesn't refill, and the renamed one still does.
        loaded.inventory.add("d")
        loaded.inventory.add("e")
        self.assertEqual(loaded.get_class("Stop").symbols, ["p", "s"])
        self.assertEqual(loaded.get_class("Vocoid").symbols, ["a", "i", "u", "e"])

    def test_defaults_cant_be_deleted(self):
        with self.assertRaises(ValueError):
            self.language.remove_class(self.language.get_class("Nasal"))

    def test_class_names_are_unique(self):
        with self.assertRaises(ValueError):
            self.language.add_class("Nasal")
        mine = self.language.add_class("Mine")
        with self.assertRaises(ValueError):
            mine.name = "Vowel"
        with self.assertRaises(ValueError):
            self.language.add_class("")

    def test_removed_phoneme_leaves_hand_edited_default(self):
        stop = self.language.get_class("Stop")
        stop.remove("b")
        self.language.inventory.remove("p")
        loaded = self.round_trip()
        self.assertEqual(loaded.get_class("Stop").symbols, [])

if __name__ == "__main__":
    unittest.main()

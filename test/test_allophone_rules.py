# test/test_allophone_rules.py

import tempfile
import os
import unittest

# Add the parent directory to the path so we can import the module we want to test
import sys
from os import path
sys.path.append(path.abspath(path.join(path.dirname(__file__), '../src')))

from wordweaver_project import WORD_BOUNDARY, Project

class TestAllophoneRules(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file = path.join(self.temp_dir.name, "test.wwproj")
        self.project = Project("Test Project")
        self.language = self.project.add_language("Test")
        self.language.inventory.set_symbols(["p", "t", "k", "n", "s", "a", "i", "u"])

    def tearDown(self):
        self.temp_dir.cleanup()

    def round_trip(self):
        self.project.save(self.file)
        return Project.load(self.file).languages[0]

    def test_class_context_round_trip(self):
        vowel = self.language.get_class("Vowel")
        rule = self.language.add_allophone_rule("t", "ɾ", before=vowel, after=vowel)
        self.assertEqual(str(rule), "/t/ → [ɾ] / Vowel _ Vowel")
        loaded = self.round_trip()
        [loaded_rule] = loaded.allophone_rules
        self.assertEqual(loaded_rule.id, rule.id)
        self.assertEqual(loaded_rule.phoneme.symbol, "t")
        self.assertEqual(loaded_rule.allophone, "ɾ")
        self.assertIs(loaded_rule.before, loaded.get_class("Vowel"))
        self.assertIs(loaded_rule.after, loaded.get_class("Vowel"))
        self.assertEqual(loaded.allophones_of("t"), ["ɾ"])

    def test_word_boundary_and_phoneme_contexts_round_trip(self):
        # Word-final devoicing and aspiration at the start of a word, plus a rule with no context.
        final = self.language.add_allophone_rule("n", "n̥", after=WORD_BOUNDARY)
        initial = self.language.add_allophone_rule("p", "pʰ", before=WORD_BOUNDARY, after="a")
        anywhere = self.language.add_allophone_rule("k", "kʷ")
        self.assertEqual(str(final), "/n/ → [n̥] / _ #")
        self.assertEqual(str(initial), "/p/ → [pʰ] / # _ a")
        self.assertEqual(str(anywhere), "/k/ → [kʷ]")
        loaded = self.round_trip()
        self.assertEqual([str(r) for r in loaded.allophone_rules], ["/n/ → [n̥] / _ #", "/p/ → [pʰ] / # _ a", "/k/ → [kʷ]"])
        rules = {r.phoneme.symbol: r for r in loaded.allophone_rules}
        self.assertIsNone(rules["n"].before)
        self.assertIs(rules["n"].after, WORD_BOUNDARY)
        self.assertIs(rules["p"].after, loaded.inventory.get("a"))
        self.assertIsNone(rules["k"].after)

    def test_edit_and_remove_rules(self):
        vowel = self.language.get_class("Vowel")
        rule = self.language.add_allophone_rule("t", "ɾ", before=vowel, after=vowel)
        gone = self.language.add_allophone_rule("s", "z", before=vowel, after=vowel)
        rule.allophone = "d"
        rule.after = WORD_BOUNDARY
        rule.phoneme = "k"
        self.language.remove_allophone_rule(gone)
        loaded = self.round_trip()
        self.assertEqual([str(r) for r in loaded.allophone_rules], ["/k/ → [d] / Vowel _ #"])
        self.assertEqual(loaded.allophones_of("k"), ["d"])
        self.assertEqual(loaded.allophones_of("s"), [])
        # The removed rule's ID was the newest one, so a reused ID would show up right after loading.
        self.assertGreater(loaded.add_allophone_rule("t", "ʔ").id, gone.id)

    def test_allophones_of_lists_each_once(self):
        self.language.add_allophone_rule("t", "ɾ", before="a", after="a")
        self.language.add_allophone_rule("t", "ʔ", after=WORD_BOUNDARY)
        self.language.add_allophone_rule("t", "ɾ", before="i", after="i")
        self.assertEqual(self.language.allophones_of("t"), ["ɾ", "ʔ"])

    def test_user_class_context(self):
        stops = self.language.add_class("Stops")
        stops.add("p")
        stops.add("k")
        self.language.add_allophone_rule("n", "ŋ", after=stops)
        loaded = self.round_trip()
        self.assertIs(loaded.allophone_rules[0].after, loaded.get_class("Stops"))

    def test_invalid_rules(self):
        other = self.project.add_language("Other")
        with self.assertRaises(ValueError):
            self.language.add_allophone_rule("ʃ", "ʒ")
        with self.assertRaises(ValueError):
            self.language.add_allophone_rule("t", "Q")
        with self.assertRaises(ValueError):
            self.language.add_allophone_rule("t", "ʰ")
        with self.assertRaises(ValueError):
            self.language.add_allophone_rule("t", "")
        with self.assertRaises(ValueError):
            self.language.add_allophone_rule("t", "ɾ", before=other.get_class("Vowel"))
        with self.assertRaises(ValueError):
            self.language.add_allophone_rule("t", "ɾ", after="ʃ")
        rule = self.language.add_allophone_rule("t", "ɾ")
        with self.assertRaises(ValueError):
            rule.allophone = "Q"
        # A whole-rule edit with one bad part changes nothing.
        with self.assertRaises(ValueError):
            rule.edit("k", "Q", WORD_BOUNDARY, None)
        self.assertEqual(str(rule), "/t/ → [ɾ]")
        self.assertEqual(len(self.language.allophone_rules), 1)

    def test_rules_drop_when_what_they_use_is_removed(self):
        mine = self.language.add_class("Mine")
        self.language.add_allophone_rule("t", "ɾ")
        self.language.add_allophone_rule("k", "x", before="a")
        self.language.add_allophone_rule("s", "z", before=mine)
        self.language.add_allophone_rule("p", "ɸ")
        self.language.inventory.remove("t")
        self.language.inventory.remove("a")
        self.language.remove_class(mine)
        self.assertEqual([str(r) for r in self.language.allophone_rules], ["/p/ → [ɸ]"])
        # Putting /t/ back makes a new Phoneme, so its old rule doesn't come back.
        self.language.inventory.add("t")
        self.assertEqual(self.language.allophones_of("t"), [])
        loaded = self.round_trip()
        self.assertEqual([str(r) for r in loaded.allophone_rules], ["/p/ → [ɸ]"])

    def test_rules_round_trip_through_patches(self):
        vowel = self.language.get_class("Vowel")
        edited = self.language.add_allophone_rule("t", "ɾ", before=vowel, after=vowel)
        removed = self.language.add_allophone_rule("k", "x")
        # Pad the file out, so the patch stays under the size where saving compacts by itself.
        for _ in range(60):
            self.project.tags.add(os.urandom(16).hex())
        self.project.save(self.file)
        with open(self.file, "rb") as f_in:
            base = f_in.read()
        # Now edit one rule, remove one, and add one, then save again as a patch.
        edited.edit("t", "ʔ", vowel, WORD_BOUNDARY)
        self.language.remove_allophone_rule(removed)
        added = self.language.add_allophone_rule("n", "ŋ", after="k")
        self.project.save()
        with open(self.file, "rb") as f_in:
            self.assertTrue(f_in.read().startswith(base))
        loaded = Project.load(self.file).languages[0]
        self.assertEqual([(r.id, str(r)) for r in loaded.allophone_rules], [(edited.id, "/t/ → [ʔ] / Vowel _ #"), (added.id, "/n/ → [ŋ] / _ k")])

if __name__ == "__main__":
    unittest.main()

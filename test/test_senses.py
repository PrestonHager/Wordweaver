# test/test_senses.py

import subprocess
import unittest

# Add the parent directory to the path so we can import the module we want to test
import sys
from os import path
SRC = path.abspath(path.join(path.dirname(__file__), '../src'))
sys.path.append(SRC)

from lexicon import ConceptReference, ConceptSource
from senses import MemorySenses, Sense, WordNetSenses, lookup_for

# A handful of real Open English WordNet 2025 senses, so tests never need the real download.
FIXTURE = path.join(path.dirname(__file__), "fixtures", "oewn_senses.json")
RIVER_BANK = "oewn-09236472-n"
MONEY_BANK = "oewn-08437235-n"

class TestSenses(unittest.TestCase):
    def setUp(self):
        self.senses = MemorySenses.from_json(FIXTURE)

    def test_nothing_loads_until_the_first_search(self):
        calls = []
        def load():
            calls.append(1)
            return [Sense(ConceptSource.OPEN_ENGLISH_WORDNET, "x-1-n", ("x",), "n", "a letter")]
        senses = MemorySenses(load)
        self.assertEqual(calls, [])
        self.assertFalse(senses.is_loaded)
        self.assertEqual([s.id for s in senses.search("x")], ["x-1-n"])
        senses.search("x")
        senses.get("x-1-n")
        self.assertEqual(calls, [1])

    def test_both_banks(self):
        banks = self.senses.search("bank")
        ids = [sense.id for sense in banks]
        self.assertIn(RIVER_BANK, ids)
        self.assertIn(MONEY_BANK, ids)
        river = self.senses.get(RIVER_BANK)
        self.assertEqual(river.lemmas, ("bank",))
        self.assertEqual(river.pos, "n")
        self.assertEqual(river.pos_name, "noun")
        self.assertIn("slope beside a body of water", river.gloss)
        self.assertEqual(river.label(), "bank (noun): sloping land (especially the slope beside a body of water)")
        self.assertIn("financial institution", self.senses.get(MONEY_BANK).gloss)

    def test_search_shows_parts_of_speech(self):
        self.assertEqual({sense.pos for sense in self.senses.search("bank")}, {"n", "v"})

    def test_search_ignores_case_spaces_and_underscores(self):
        self.assertEqual([s.id for s in self.senses.search("  River ")], ["oewn-09434308-n"])
        self.assertEqual([s.id for s in self.senses.search("savings_bank")], ["oewn-04146942-n"])
        self.assertEqual([s.id for s in self.senses.search("h2o")], ["oewn-14869913-n"])

    def test_no_matches(self):
        self.assertEqual(self.senses.search("zebra"), [])
        self.assertEqual(self.senses.search(""), [])
        self.assertIsNone(self.senses.get("oewn-00000000-n"))

    def test_sense_gives_its_reference(self):
        reference = self.senses.get(RIVER_BANK).reference
        self.assertEqual(reference, ConceptReference(ConceptSource.OPEN_ENGLISH_WORDNET, RIVER_BANK))
        self.assertEqual(str(reference), "oewn:oewn-09236472-n")

    def test_lookup_for_gloss_language(self):
        self.assertIsInstance(lookup_for("en"), WordNetSenses)
        self.assertIsInstance(lookup_for("en-GB"), WordNetSenses)
        self.assertIs(lookup_for("en"), lookup_for("en-US"))
        # Other Gloss Languages get Open Multilingual Wordnet later, in #48.
        self.assertIsNone(lookup_for("fr"))

    def test_startup_doesnt_load_dictionary(self):
        # Import the app and make a lookup in a fresh Python, then check wn was never imported.
        code = ("import sys; sys.path.insert(0, sys.argv[1]); import main, senses; senses.lookup_for('en'); "
                "print('wn' in sys.modules)")
        result = subprocess.run([sys.executable, "-c", code, SRC], capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "False")

class TestConceptReference(unittest.TestCase):
    def test_text_round_trip(self):
        for source, prefix in ((ConceptSource.OPEN_ENGLISH_WORDNET, "oewn"),
                               (ConceptSource.OPEN_MULTILINGUAL_WORDNET, "omw"),
                               (ConceptSource.CONCEPTICON, "concepticon")):
            with self.subTest(source=source):
                reference = ConceptReference(source, "id-1")
                self.assertEqual(str(reference), f"{prefix}:id-1")
                self.assertEqual(ConceptReference.parse(str(reference)), reference)

    def test_bad_references(self):
        with self.assertRaises(ValueError):
            ConceptReference(ConceptSource.OPEN_ENGLISH_WORDNET, "  ")
        with self.assertRaises(ValueError):
            ConceptReference(1, "oewn-09236472-n")
        with self.assertRaises(ValueError):
            ConceptReference.parse("oewn-09236472-n")
        with self.assertRaises(ValueError):
            ConceptReference.parse("wiktionary:bank")

    def test_id_is_trimmed(self):
        self.assertEqual(ConceptReference(ConceptSource.CONCEPTICON, " 1234 ").id, "1234")

if __name__ == "__main__":
    unittest.main()

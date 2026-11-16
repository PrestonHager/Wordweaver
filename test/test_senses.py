# test/test_senses.py

import subprocess
import tempfile
import unittest
from types import SimpleNamespace

# Add the parent directory to the path so we can import the module we want to test
import sys
from os import path
SRC = path.abspath(path.join(path.dirname(__file__), '../src'))
sys.path.append(SRC)

from lexicon import ConceptReference, ConceptSource
from senses import MemorySenses, OmwSenses, Sense, WordNetSenses, lookup_for, omw_gloss, wordnet_languages

# A handful of real Open English WordNet 2025 senses, so tests never need the real download.
FIXTURE = path.join(path.dirname(__file__), "fixtures", "oewn_senses.json")
# A few real French senses from Open Multilingual Wordnet 2.0, as OmwSenses gives them, with English glosses from the ILI.
FRENCH_FIXTURE = path.join(path.dirname(__file__), "fixtures", "omw_fr_senses.json")
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
        self.assertIsInstance(lookup_for("fr"), OmwSenses)

    def test_startup_doesnt_load_dictionary(self):
        # Import the app and make a lookup in a fresh Python, then check wn was never imported.
        code = ("import sys; sys.path.insert(0, sys.argv[1]); import main, senses; senses.lookup_for('en'); "
                "print('wn' in sys.modules)")
        result = subprocess.run([sys.executable, "-c", code, SRC], capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "False")

class TestOmwSenses(unittest.TestCase):
    def setUp(self):
        self.senses = MemorySenses.from_json(FRENCH_FIXTURE, ConceptSource.OPEN_MULTILINGUAL_WORDNET)

    def test_search_in_french(self):
        self.assertEqual([s.id for s in self.senses.search("banque")], ["i85041", "i81364", "i33287"])
        self.assertEqual([s.id for s in self.senses.search("Rive")], ["i85041", "i86079"])
        self.assertEqual([s.id for s in self.senses.search("eau minérale")], ["i79021"])
        self.assertEqual(self.senses.search("bank"), [])

    def test_reference_uses_the_ili(self):
        river = self.senses.get("i85041")
        self.assertEqual(river.reference, ConceptReference(ConceptSource.OPEN_MULTILINGUAL_WORDNET, "i85041"))
        self.assertEqual(str(river.reference), "omw:i85041")
        self.assertEqual(ConceptReference.parse("omw:i85041"), river.reference)
        self.assertEqual(river.label(), "rive, banque (noun): (English) sloping land (especially the slope beside a body of water)")

    def test_gloss_falls_back_to_english_then_lemmas(self):
        self.assertEqual(omw_gloss("rive d'un cours d'eau", "sloping land"), "rive d'un cours d'eau")
        self.assertEqual(omw_gloss(None, "sloping land"), "(English) sloping land")
        self.assertEqual(omw_gloss(None, None), "")
        sense = Sense(ConceptSource.OPEN_MULTILINGUAL_WORDNET, "i85041", ("rive", "banque"), "n", "")
        self.assertEqual(sense.label(), "rive, banque (noun)")

    def test_synsets_become_senses(self):
        # Stand in for wn's synsets and the ILI, so this runs without the real data.
        class FakeOmw(OmwSenses):
            def _english_definition(self, ili_id):
                return {"i85041": "sloping land"}.get(ili_id)
        def synset(id, ili, definition=None):
            return SimpleNamespace(id=id, ili=ili, pos="n", lemmas=lambda: ["rive", "banque"], definition=lambda: definition)
        omw = FakeOmw("omw-fr:2.0", "French")
        self.assertEqual(omw._sense(synset("omw-fr-09213565-n", "i85041")),
                         Sense(ConceptSource.OPEN_MULTILINGUAL_WORDNET, "i85041", ("rive", "banque"), "n", "(English) sloping land"))
        self.assertEqual(omw._sense(synset("omw-fr-09213565-n", "i85041", "terrain en pente")).gloss, "terrain en pente")
        # A synset with no ILI keeps its own ID, and has only its lemmas to show.
        orphan = omw._sense(synset("omw-fr-99999999-n", None))
        self.assertEqual((orphan.id, orphan.gloss), ("omw-fr-99999999-n", ""))

    def test_get_by_ili_or_synset_id(self):
        import wn
        river = SimpleNamespace(id="omw-fr-09213565-n", ili=None, pos="n", lemmas=lambda: ["rive"], definition=lambda: "rive")
        class FakeWordnet:
            def synsets(self, ili=None):
                return [river] if ili == "i85041" else []
            def synset(self, id):
                if id != river.id:
                    raise wn.Error(f"no synset {id}")
                return river
        with tempfile.TemporaryDirectory() as data_dir:
            omw = OmwSenses("omw-fr:2.0", "French", data_dir)
            omw._wordnet = FakeWordnet()  # pyright: ignore[reportAttributeAccessIssue]  A fake is enough here.
            self.assertEqual(omw.get("i85041").lemmas, ("rive",))
            self.assertEqual(omw.get("omw-fr-09213565-n").lemmas, ("rive",))
            self.assertIsNone(omw.get("i0"))
            self.assertIsNone(omw.get("omw-fr-00000000-n"))

    def test_lookup_for_other_gloss_languages(self):
        french = lookup_for("fr")
        self.assertIsInstance(french, OmwSenses)
        self.assertEqual(french.source, ConceptSource.OPEN_MULTILINGUAL_WORDNET)
        self.assertEqual(french.name, "Open Multilingual Wordnet (French)")
        self.assertEqual(french._lexicon, "omw-fr:2.0")  # pyright: ignore[reportAttributeAccessIssue]  Only OmwSenses has _lexicon.
        self.assertIs(lookup_for("fr-CA"), french)
        self.assertEqual(lookup_for("es")._lexicon, "omw-es:2.0")  # pyright: ignore[reportAttributeAccessIssue]  Only OmwSenses has _lexicon.
        self.assertEqual(lookup_for("ja")._lexicon, "omw-ja:2.0")  # pyright: ignore[reportAttributeAccessIssue]  Only OmwSenses has _lexicon.
        self.assertIs(lookup_for("cmn"), lookup_for("zh-Hans"))
        self.assertIsNot(lookup_for("es"), french)
        # Some languages have no open wordnet at all, so they can't link senses.
        self.assertIsNone(lookup_for("de"))
        self.assertIsNone(lookup_for("tok"))

    def test_every_listed_language_has_a_wordnet(self):
        languages = wordnet_languages()
        self.assertEqual(languages[0], ("English", "en"))
        self.assertIn(("French", "fr"), languages)
        self.assertEqual(len({code for _name, code in languages}), len(languages))
        for name, code in languages:
            with self.subTest(code=code):
                self.assertIsNotNone(lookup_for(code))

    def test_startup_doesnt_load_french_dictionary(self):
        code = ("import sys; sys.path.insert(0, sys.argv[1]); import main, senses; senses.lookup_for('fr'); "
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
            ConceptReference(1, "oewn-09236472-n")  # pyright: ignore[reportArgumentType]  Wrong on purpose.
        with self.assertRaises(ValueError):
            ConceptReference.parse("oewn-09236472-n")
        with self.assertRaises(ValueError):
            ConceptReference.parse("wiktionary:bank")

    def test_id_is_trimmed(self):
        self.assertEqual(ConceptReference(ConceptSource.CONCEPTICON, " 1234 ").id, "1234")

if __name__ == "__main__":
    unittest.main()

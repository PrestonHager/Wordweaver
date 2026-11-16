# test/test_concepticon.py

import csv
import io
import tempfile
import unittest
from pathlib import Path

# Add the parent directory to the path so we can import the module we want to test
import sys
from os import path
sys.path.append(path.abspath(path.join(path.dirname(__file__), '../src')))

from concepticon import LISTS_DIR, ConceptList, ConcepticonSenses, concept_lists
from lexicon import ConceptReference, ConceptSource, Form
from lexicon_csv import split_values
from senses import NotDownloadedError
from wordweaver_project import Project

# Six real concepts from the Swadesh 100 and ten rows of the real Concepticon table, so tests never need the network.
FIXTURES = Path(__file__).parent / "fixtures"
CONCEPT_LIST = FIXTURES / "concept_list.json"
CONCEPT_TABLE = FIXTURES / "concepticon_concepts.tsv"

def concepticon(id: str) -> ConceptReference:
    return ConceptReference(ConceptSource.CONCEPTICON, id)

class TestSeeding(unittest.TestCase):
    def setUp(self):
        self.project = Project("Test Project")
        self.language = self.project.add_language("Test")
        self.lexicon = self.language.lexicon
        self.concepts = ConceptList.load(CONCEPT_LIST)

    def test_loads_list_in_order(self):
        self.assertEqual(self.concepts.name, "Test Swadesh 6")
        self.assertEqual(len(self.concepts), 6)
        self.assertEqual([c.id for c in self.concepts], ["98", "646", "323", "1277", "1209", "948"])
        self.assertEqual(self.concepts.concepts[3].gloss, "HAND")
        self.assertIn("fore limb", self.concepts.concepts[3].definition)
        self.assertEqual(self.concepts.license, "CC-BY-4.0")

    def test_seed_makes_one_unfinished_entry_per_concept(self):
        added = self.lexicon.seed_from_concept_list(self.concepts)
        self.assertEqual(list(self.lexicon), added)
        self.assertEqual([entry.form for entry in added], [Form()] * 6)
        self.assertTrue(all(entry.is_unfinished for entry in added))
        # The list's English word is the Gloss, or Concepticon's gloss in lower case when there isn't one.
        self.assertEqual([entry.glosses for entry in added],
                         [("all",), ("ashes",), ("fat (grease)",), ("hand",), ("I",), ("water",)])
        self.assertEqual([entry.definitions[0].concept_reference for entry in added],
                         [concepticon(id) for id in ("98", "646", "323", "1277", "1209", "948")])

    def test_seeding_again_skips_linked_concepts(self):
        self.lexicon.seed_from_concept_list(self.concepts)
        self.assertEqual(self.lexicon.seed_from_concept_list(self.concepts), [])
        self.assertEqual(len(self.lexicon), 6)

    def test_skips_concepts_you_already_linked(self):
        # You already have a word for water, linked by hand, and filled in a Form for "hand" after seeding once.
        water = self.lexicon.add("akwa", ["water"])
        self.lexicon.set_concept_reference(water, water.definitions[0], concepticon("948"))
        self.lexicon.seed_from_concept_list(list(self.concepts)[:4])
        hand = self.lexicon.unfinished()[-1]
        self.lexicon.edit(hand, form="mano")
        added = self.lexicon.seed_from_concept_list(self.concepts)
        self.assertEqual([entry.glosses for entry in added], [("I",)])
        self.assertEqual(len(self.lexicon), 6)

    def test_seeding_doesnt_touch_other_languages(self):
        other = self.project.add_language("Other")
        self.lexicon.seed_from_concept_list(self.concepts)
        self.assertEqual(len(other.lexicon.seed_from_concept_list(self.concepts)), 6)

    def test_unfinished(self):
        self.lexicon.add("ta", ["one"])
        added = self.lexicon.seed_from_concept_list(self.concepts)
        self.assertEqual(self.lexicon.unfinished(), added)
        self.lexicon.edit(added[0], form="toto")
        self.assertFalse(added[0].is_unfinished)
        self.assertEqual(self.lexicon.unfinished(), added[1:])

    def test_seeded_entries_round_trip(self):
        self.lexicon.seed_from_concept_list(self.concepts)
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "seeded.wwproj"
            self.project.save(file)
            loaded = Project.load(file).languages[0].lexicon
        self.assertEqual([(e.id, e.form, e.glosses, e.definitions[0].concept_reference) for e in loaded],
                         [(e.id, e.form, e.glosses, e.definitions[0].concept_reference) for e in self.lexicon])
        self.assertEqual(len(loaded.unfinished()), 6)
        # Seeding the loaded Lexicon still knows what's already there.
        self.assertEqual(loaded.seed_from_concept_list(self.concepts), [])

    def test_seeded_entries_export_to_csv(self):
        self.lexicon.seed_from_concept_list(self.concepts)
        rows = list(csv.reader(io.StringIO(self.project.export_lexicon_csv(self.language)[1:], newline="")))[1:]
        self.assertEqual(len(rows), 6)
        self.assertEqual([row[1] for row in rows], [""] * 6)
        self.assertEqual(split_values(rows[3][3]), ["hand"])
        self.assertEqual(rows[3][6], "concepticon:1277")
        self.assertEqual(ConceptReference.parse(rows[5][6]), concepticon("948"))

class TestShippedLists(unittest.TestCase):
    def test_swadesh_100(self):
        lists = {concept_list.id: concept_list for concept_list in concept_lists()}
        swadesh = lists["Swadesh-1955-100"]
        self.assertEqual(len(swadesh), 100)
        self.assertEqual(len({concept.id for concept in swadesh}), 100)
        self.assertEqual([c.number for c in swadesh][:3], ["1", "2", "3"])
        self.assertTrue(all(concept.seed_gloss and concept.definition for concept in swadesh))
        # The data is CC-BY 4.0, so it has to say who to credit.
        self.assertEqual(swadesh.license, "CC-BY-4.0")
        self.assertIn("Concepticon v3.4.0", swadesh.attribution)
        self.assertIn("v3.4.0", swadesh.source)

    def test_lists_ship_with_the_app(self):
        spec = (Path(__file__).parent.parent / "Wordweaver.spec").read_text(encoding="utf-8")
        self.assertEqual(LISTS_DIR.name, "concept_lists")
        self.assertIn("('src/concept_lists/', 'concept_lists/')", spec)

class TestConcepticonSenses(unittest.TestCase):
    def setUp(self):
        self.senses = ConcepticonSenses(CONCEPT_TABLE)

    def test_search_puts_exact_match_first(self):
        found = [(s.lemmas[0], s.id) for s in self.senses.search("Water")]
        self.assertEqual(found[0], ("WATER", "948"))
        self.assertIn(("BOILED WATER", "3362"), found)
        # Whole words only, so a waterfall isn't water.
        self.assertNotIn("WATERFALL", [gloss for gloss, _id in found])
        self.assertEqual([s.id for s in self.senses.search("hand")], ["1277", "2121"])
        self.assertEqual(self.senses.search("zebra"), [])
        self.assertEqual(self.senses.search("  "), [])

    def test_sense(self):
        water = self.senses.get("948")
        self.assertEqual(water.reference, concepticon("948"))
        self.assertEqual(water.lemmas, ("WATER",))
        self.assertEqual(water.pos_name, "person/thing")
        self.assertTrue(water.gloss.startswith("Common liquid (H₂O)"))
        self.assertIsNone(self.senses.get("99999"))

    def test_download(self):
        with tempfile.TemporaryDirectory() as folder:
            # A file URL stands in for GitHub, so this stays offline.
            senses = ConcepticonSenses(Path(folder) / "data" / "concepticon.tsv", url=CONCEPT_TABLE.as_uri())
            self.assertFalse(senses.is_downloaded())
            with self.assertRaises(NotDownloadedError):
                senses.search("water")
            senses.download()
            self.assertTrue(senses.is_downloaded())
            self.assertEqual(senses.search("water")[0].id, "948")

if __name__ == "__main__":
    unittest.main()

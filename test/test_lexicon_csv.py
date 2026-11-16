# test/test_lexicon_csv.py

import csv
import io
import unittest
import tempfile

# Add the parent directory to the path so we can import the module we want to test
import sys
from os import path
sys.path.append(path.abspath(path.join(path.dirname(__file__), '../src')))

from lexicon import ConceptReference, ConceptSource, Form
from lexicon_csv import HEADER, join_values, split_values
from wordweaver_project import Project

class TestLexiconCsv(unittest.TestCase):
    def setUp(self):
        self.project = Project("Test Project")
        self.language = self.project.add_language("Test")
        self.language.inventory.set_symbols(["t͡s", "t", "s", "a", "i", "ŋ", "ʃ", "ə"])
        self.lexicon = self.language.lexicon

    def export(self) -> str:
        return self.project.export_lexicon_csv(self.language)

    def rows(self) -> list[list[str]]:
        # Read the export back like a spreadsheet would, after dropping the byte order mark.
        text = self.export()
        self.assertTrue(text.startswith("﻿"))
        return list(csv.reader(io.StringIO(text[1:], newline="")))

    def test_header(self):
        rows = self.rows()
        self.assertEqual(tuple(rows[0]), HEADER)
        self.assertEqual(rows[0], ["Entry ID", "Form", "Definition", "Glosses", "Technical Terms", "Description", "Concept Reference", "Tags"])
        self.assertEqual(len(rows), 1)

    def test_round_trip(self):
        animals = self.project.tags.add("animals")
        sacred = self.project.tags.add("sacred; holy, \"old\"")
        water = self.lexicon.add(Form.parse("t͡saŋ", self.language.inventory.symbols), ["water", "river water"], terms=["mass noun"], description="Fresh water, not \"sea\" water, from a spring.\nAlso rain.")
        self.lexicon.tag(water, sacred)
        fish = self.lexicon.add("ʃəti", ["fish; trout", "back\\slash", "a, b"], terms=["count noun", "inanimate"])
        self.lexicon.tag(fish, animals)
        self.lexicon.tag(fish, sacred)
        self.lexicon.set_concept_reference(water, water.definitions[0], ConceptReference(ConceptSource.OPEN_ENGLISH_WORDNET, "oewn-14869913-n"))
        rows = self.rows()[1:]
        self.assertEqual([row[0] for row in rows], [str(water.id), str(fish.id)])
        self.assertEqual([row[1] for row in rows], ["t͡saŋ", "ʃəti"])
        self.assertEqual([row[2] for row in rows], ["1", "1"])
        self.assertEqual([split_values(row[3]) for row in rows], [["water", "river water"], ["fish; trout", "back\\slash", "a, b"]])
        self.assertEqual([split_values(row[4]) for row in rows], [["mass noun"], ["count noun", "inanimate"]])
        self.assertEqual([row[5] for row in rows], ["Fresh water, not \"sea\" water, from a spring.\nAlso rain.", ""])
        self.assertEqual([row[6] for row in rows], ["oewn:oewn-14869913-n", ""])
        self.assertEqual(ConceptReference.parse(rows[0][6]), water.definitions[0].concept_reference)
        self.assertEqual([split_values(row[7]) for row in rows], [["sacred; holy, \"old\""], ["animals", "sacred; holy, \"old\""]])

    def test_concept_reference_per_definition(self):
        # The two "bank"s as Homophones, plus Polysemy with one linked and one unlinked Definition.
        river = ConceptReference(ConceptSource.OPEN_ENGLISH_WORDNET, "oewn-09236472-n")
        money = ConceptReference(ConceptSource.OPEN_ENGLISH_WORDNET, "oewn-08437235-n")
        shore = self.lexicon.add("sat", ["bank"])
        self.lexicon.set_concept_reference(shore, shore.definitions[0], river)
        vault = self.lexicon.add("sat", ["bank"])
        self.lexicon.add_definition(vault, ["treasury"])
        self.lexicon.set_concept_reference(vault, vault.definitions[0], money)
        rows = self.rows()[1:]
        self.assertEqual([row[6] for row in rows], ["oewn:oewn-09236472-n", "oewn:oewn-08437235-n", ""])
        self.assertEqual([ConceptReference.parse(row[6]) for row in rows if row[6]], [river, money])

    def test_polysemy_gives_a_row_per_definition(self):
        path_entry = self.lexicon.add("sat", ["river"], description="Running water.")
        self.lexicon.add_definition(path_entry, ["road", "path"], terms=["metaphor"])
        self.lexicon.add_definition(path_entry, ["journey"], index=0)
        rows = self.rows()[1:]
        self.assertEqual([row[0] for row in rows], [str(path_entry.id)] * 3)
        self.assertEqual([row[1] for row in rows], ["sat"] * 3)
        self.assertEqual([row[2] for row in rows], ["1", "2", "3"])
        self.assertEqual([split_values(row[3]) for row in rows], [["journey"], ["river"], ["road", "path"]])
        self.assertEqual([split_values(row[4]) for row in rows], [[], [], ["metaphor"]])
        self.assertEqual([row[5] for row in rows], ["", "Running water.", ""])

    def test_empty_form(self):
        self.lexicon.add("", ["to see"])
        rows = self.rows()[1:]
        self.assertEqual(rows[0][1], "")
        self.assertEqual(split_values(rows[0][3]), ["to see"])

    def test_renamed_tag_shows_new_name(self):
        tag = self.project.tags.add("animals")
        entry = self.lexicon.add("ta", ["dog"])
        self.lexicon.tag(entry, tag)
        self.project.tags.rename(tag, "beasts")
        self.assertEqual(split_values(self.rows()[1][7]), ["beasts"])

    def test_only_exports_one_language(self):
        other = self.project.add_language("Other")
        other.lexicon.add("si", ["two"])
        self.lexicon.add("ta", ["one"])
        rows = self.rows()[1:]
        self.assertEqual([split_values(row[3]) for row in rows], [["one"]])

    def test_language_not_in_project(self):
        other = Project("Other").add_language("Other")
        with self.assertRaises(ValueError):
            self.project.export_lexicon_csv(other)

    def test_saved_file_has_bom(self):
        self.lexicon.add("ŋi", ["eye"])
        with tempfile.TemporaryDirectory() as temp_dir:
            file = path.join(temp_dir, "lexicon.csv")
            # Write it the same way the app does.
            with open(file, "w", encoding="utf-8", newline="") as f:
                f.write(self.export())
            with open(file, "rb") as f:
                data = f.read()
            self.assertTrue(data.startswith(b"\xef\xbb\xbf"))
            self.assertNotIn(b"\r\r\n", data)
            with open(file, encoding="utf-8-sig", newline="") as f:
                rows = list(csv.reader(f))
        self.assertEqual(rows[1][1], "ŋi")

    def test_values_round_trip(self):
        cases = [[], ["a"], ["a", "b"], ["a; b", "c"], [";", "\\", "\\;", ";\\"], ["x ", " y"], ["", "z"]]
        for values in cases:
            with self.subTest(values=values):
                self.assertEqual(split_values(join_values(values)), values)
        self.assertEqual(join_values(["a;b", "c\\d"]), "a\\;b; c\\\\d")

if __name__ == "__main__":
    unittest.main()

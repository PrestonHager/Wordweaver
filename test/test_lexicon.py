# test/test_lexicon.py

import unittest
import tempfile

# Add the parent directory to the path so we can import the module we want to test
import sys
from os import path
sys.path.append(path.abspath(path.join(path.dirname(__file__), '../src')))

from lexicon import Form
from wordweaver_project import Project

class TestLexicon(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file = path.join(self.temp_dir.name, "test.wwproj")
        self.project = Project("Test Project")
        self.language = self.project.add_language("Test")
        self.language.inventory.set_symbols(["t͡s", "t", "s", "a", "i", "ŋ"])
        self.lexicon = self.language.lexicon

    def tearDown(self):
        self.temp_dir.cleanup()

    def round_trip(self) -> Project:
        self.project.save(self.file)
        return Project.load(self.file)

    def entries(self, lexicon) -> list[tuple]:
        # Boil each Entry down to what you can see, so two Lexicons can be compared.
        return [(e.id, e.form.phonemes, [(d.id, d.glosses, d.terms, d.description) for d in e.definitions]) for e in lexicon]

    def test_round_trip(self):
        self.lexicon.add(Form.parse("t͡sata", self.language.inventory.symbols), ["water", "river water"])
        self.lexicon.add("ŋi", ["eye"])
        self.lexicon.add("", ["to see"])
        loaded = self.round_trip().languages[0].lexicon
        self.assertEqual(self.entries(loaded), self.entries(self.lexicon))
        self.assertEqual([str(e.form) for e in loaded], ["t͡sata", "ŋi", ""])
        self.assertEqual([e.glosses for e in loaded], [("water", "river water"), ("eye",), ("to see",)])

    def test_each_language_keeps_its_own_lexicon(self):
        other = self.project.add_language("Other")
        self.lexicon.add("ta", ["one"])
        other.lexicon.add("si", ["two"])
        other.lexicon.add("sa", ["three"])
        loaded = self.round_trip()
        self.assertEqual([e.glosses for e in loaded.languages[0].lexicon], [("one",)])
        self.assertEqual([e.glosses for e in loaded.languages[1].lexicon], [("two",), ("three",)])

    def test_entry_has_one_definition(self):
        entry = self.lexicon.add("ta", ["one", "single"])
        self.assertEqual(len(entry.definitions), 1)
        self.assertEqual(entry.definitions[0].glosses, ("one", "single"))

    def test_entry_needs_a_gloss(self):
        with self.assertRaises(ValueError):
            self.lexicon.add("ta", [])
        with self.assertRaises(ValueError):
            self.lexicon.add("ta", ["", "  "])
        self.assertEqual(len(self.lexicon), 0)

    def test_blank_glosses_are_dropped(self):
        entry = self.lexicon.add("ta", [" one ", "", "single"])
        self.assertEqual(entry.glosses, ("one", "single"))

    def test_edit_round_trip(self):
        entry = self.lexicon.add("ta", ["one"])
        ids = (entry.id, entry.definitions[0].id)
        self.lexicon.edit(entry, form="sa", glosses=["two", "pair"])
        loaded = self.round_trip().languages[0].lexicon
        [loaded_entry] = list(loaded)
        self.assertEqual((loaded_entry.id, loaded_entry.definitions[0].id), ids)
        self.assertEqual(str(loaded_entry.form), "sa")
        self.assertEqual(loaded_entry.glosses, ("two", "pair"))

    def test_edit_only_form_or_glosses(self):
        entry = self.lexicon.add("ta", ["one"])
        self.lexicon.edit(entry, form="sa")
        self.assertEqual((str(entry.form), entry.glosses), ("sa", ("one",)))
        self.lexicon.edit(entry, glosses=["two"])
        self.assertEqual((str(entry.form), entry.glosses), ("sa", ("two",)))

    def test_bad_edit_changes_nothing(self):
        entry = self.lexicon.add("ta", ["one"])
        with self.assertRaises(ValueError):
            self.lexicon.edit(entry, form="sa", glosses=[""])
        self.assertEqual((str(entry.form), entry.glosses), ("ta", ("one",)))

    def test_remove_round_trip(self):
        first = self.lexicon.add("ta", ["one"])
        second = self.lexicon.add("si", ["two"])
        self.lexicon.remove(first)
        self.assertNotIn(first, self.lexicon)
        loaded = self.round_trip().languages[0].lexicon
        self.assertEqual(self.entries(loaded), self.entries(self.lexicon))
        self.assertEqual([e.id for e in loaded], [second.id])

    def test_remove_missing_entry(self):
        entry = self.project.add_language("Other").lexicon.add("ta", ["one"])
        with self.assertRaises(KeyError):
            self.lexicon.remove(entry)
        with self.assertRaises(KeyError):
            self.lexicon.edit(entry, form="sa")

    def test_ids_are_unique(self):
        first = self.lexicon.add("ta", ["one"])
        second = self.lexicon.add("ta", ["one"])
        ids = [p.id for p in self.language.inventory] + [self.language.id]
        ids += [first.id, first.definitions[0].id, second.id, second.definitions[0].id]
        self.assertEqual(len(ids), len(set(ids)))

    def test_ids_are_never_reused(self):
        entry = self.lexicon.add("ta", ["one"])
        removed_ids = (entry.id, entry.definitions[0].id)
        self.lexicon.remove(entry)
        # The removed Entry's IDs were the newest ones, so a reused ID would show up right after loading.
        loaded = self.round_trip().languages[0].lexicon
        new = loaded.add("ta", ["one"])
        self.assertGreater(min(new.id, new.definitions[0].id), max(removed_ids))

    def test_get_by_id(self):
        entry = self.lexicon.add("ta", ["one"])
        loaded = self.round_trip().languages[0].lexicon
        self.assertEqual(loaded.get(entry.id).glosses, ("one",))
        self.assertIsNone(loaded.get(entry.id + 1000))

    def test_entries_are_coinages(self):
        self.lexicon.add("ta", ["one"])
        [entry] = list(self.round_trip().languages[0].lexicon)
        self.assertEqual(entry.etymons, ())
        self.assertTrue(entry.is_coinage)

    def test_polysemy_round_trip(self):
        entry = self.lexicon.add("ta", ["river"], terms=["noun"], description="A big stream of water.")
        self.lexicon.add_definition(entry, ["road", "path", "way"], terms=["noun", "inalienable"])
        self.lexicon.add_definition(entry, ["to travel"], description="Going a long way, by water or by land.")
        self.lexicon.add("si", ["eye"])
        loaded = self.round_trip().languages[0].lexicon
        self.assertEqual(self.entries(loaded), self.entries(self.lexicon))
        definitions = loaded.get(entry.id).definitions
        self.assertEqual([d.glosses for d in definitions], [("river",), ("road", "path", "way"), ("to travel",)])
        self.assertEqual([d.terms for d in definitions], [("noun",), ("noun", "inalienable"), ()])
        self.assertEqual([d.description for d in definitions], ["A big stream of water.", "", "Going a long way, by water or by land."])

    def test_definition_order_round_trip(self):
        # Newer Definitions have bigger IDs, so put them first to check the order isn't just ID order.
        entry = self.lexicon.add("ta", ["first"])
        last = self.lexicon.add_definition(entry, ["last"])
        self.lexicon.add_definition(entry, ["inserted"], index=0)
        self.lexicon.move_definition(entry, last, 0)
        self.assertEqual([d.glosses for d in entry.definitions], [("last",), ("inserted",), ("first",)])
        loaded = self.round_trip().languages[0].lexicon
        self.assertEqual(self.entries(loaded), self.entries(self.lexicon))

    def test_edit_definition_round_trip(self):
        entry = self.lexicon.add("ta", ["one"])
        second = self.lexicon.add_definition(entry, ["two"], terms=["dual"], description="A pair.")
        self.lexicon.edit_definition(entry, second, glosses=["pair", "couple"], description="")
        self.assertEqual((second.glosses, second.terms, second.description), (("pair", "couple"), ("dual",), ""))
        self.lexicon.edit_definition(entry, second, terms=[" ", "dual", "count "])
        self.assertEqual(second.terms, ("dual", "count"))
        loaded = self.round_trip().languages[0].lexicon
        self.assertEqual(self.entries(loaded), self.entries(self.lexicon))

    def test_bad_definition_edit_changes_nothing(self):
        entry = self.lexicon.add("ta", ["one"], terms=["numeral"])
        definition = entry.definitions[0]
        with self.assertRaises(ValueError):
            self.lexicon.edit_definition(entry, definition, glosses=[" "], terms=[])
        self.assertEqual((definition.glosses, definition.terms), (("one",), ("numeral",)))
        with self.assertRaises(ValueError):
            self.lexicon.add_definition(entry, [])
        self.assertEqual(len(entry.definitions), 1)

    def test_remove_definition_round_trip(self):
        entry = self.lexicon.add("ta", ["one"])
        second = self.lexicon.add_definition(entry, ["two"])
        self.lexicon.remove_definition(entry, entry.definitions[0])
        loaded = self.round_trip().languages[0].lexicon
        self.assertEqual([d.id for d in loaded.get(entry.id).definitions], [second.id])
        self.assertEqual(loaded.get(entry.id).glosses, ("two",))

    def test_last_definition_cant_be_removed(self):
        entry = self.lexicon.add("ta", ["one"])
        with self.assertRaises(ValueError):
            self.lexicon.remove_definition(entry, entry.definitions[0])
        self.assertEqual(entry.glosses, ("one",))

    def test_definition_must_be_on_the_entry(self):
        entry = self.lexicon.add("ta", ["one"])
        other = self.lexicon.add("si", ["two"])
        with self.assertRaises(KeyError):
            self.lexicon.remove_definition(entry, other.definitions[0])
        with self.assertRaises(KeyError):
            self.lexicon.edit_definition(entry, other.definitions[0], glosses=["three"])
        with self.assertRaises(KeyError):
            self.lexicon.move_definition(entry, other.definitions[0], 0)

    def test_edit_changes_the_first_definition(self):
        entry = self.lexicon.add("ta", ["one"])
        self.lexicon.add_definition(entry, ["two"])
        self.lexicon.edit(entry, glosses=["uno"])
        self.assertEqual([d.glosses for d in entry.definitions], [("uno",), ("two",)])

    def test_many_entries(self):
        for i in range(2000):
            self.lexicon.add("ta" * (i % 5 + 1), [f"gloss {i}"])
        loaded = self.round_trip().languages[0].lexicon
        self.assertEqual(self.entries(loaded), self.entries(self.lexicon))

class TestForm(unittest.TestCase):
    def test_parse_matches_longest_symbol(self):
        form = Form.parse("t͡sats", ["t", "s", "t͡s", "a"])
        self.assertEqual(form.phonemes, ("t͡s", "a", "t", "s"))

    def test_parse_without_inventory(self):
        # Combining marks stay with the letter before them.
        self.assertEqual(Form.parse("ãb").phonemes, ("ã", "b"))

    def test_parse_ignores_spaces(self):
        self.assertEqual(str(Form.parse(" t a ")), "ta")

if __name__ == "__main__":
    unittest.main()

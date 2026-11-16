# test/test_wordweaver_project.py

import unittest
import tempfile

# Add the parent directory to the path so we can import the module we want to test
import sys
from os import path
sys.path.append(path.abspath(path.join(path.dirname(__file__), '../src')))

from wordweaver_project import Project, ProjectFileError

DEFAULT_PROJECT = path.abspath(path.join(path.dirname(__file__), '../src/default.wwproj'))
STARTER_PHONEMES = ["n", "p", "b", "d", "k", "ɾ", "f", "s", "l", "a", "e", "i", "o", "u"]

class TestProject(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file = path.join(self.temp_dir.name, "test.wwproj")

    def tearDown(self):
        self.temp_dir.cleanup()

    def round_trip(self, project: Project) -> Project:
        project.save(self.file)
        return Project.load(self.file)

    def test_round_trip(self):
        project = Project("Test Project")
        language = project.add_language("Proto-Test")
        language.inventory.set_symbols(["p", "d", "n", "ǀ", "a", "i", "ə", "u", "ɯ"])
        loaded = self.round_trip(project)
        self.assertEqual(loaded.name, "Test Project")
        self.assertEqual(len(loaded.languages), 1)
        self.assertEqual(loaded.languages[0].name, "Proto-Test")
        self.assertEqual(loaded.languages[0].inventory.symbols, ["p", "d", "n", "ǀ", "a", "i", "ə", "u", "ɯ"])

    def test_empty_project(self):
        loaded = self.round_trip(Project(""))
        self.assertEqual(loaded.name, "")
        self.assertEqual(loaded.languages, [])

    def test_long_names(self):
        # The old format capped lengths at 255, so check we're well past that.
        name = "Long name " * 100
        project = Project(name)
        project.add_language(name)
        loaded = self.round_trip(project)
        self.assertEqual(loaded.name, name)
        self.assertEqual(loaded.languages[0].name, name)

    def test_inventory_is_one_set(self):
        project = Project("Test Project")
        inventory = project.add_language("Test").inventory
        first = inventory.add("p")
        self.assertIs(inventory.add("p"), first)
        inventory.add("a")
        self.assertEqual(len(inventory), 2)
        self.assertIn("p", inventory)
        self.assertIn("a", inventory)
        self.assertTrue(inventory.get("a").ipa.is_vowel)

    def test_invalid_phoneme(self):
        inventory = Project("Test Project").add_language("Test").inventory
        with self.assertRaises(ValueError):
            inventory.add("Q")
        with self.assertRaises(ValueError):
            inventory.set_symbols(["p", "Q"])
        self.assertEqual(len(inventory), 0)

    def test_ids_survive_save_and_load(self):
        project = Project("Test Project")
        language = project.add_language("Test")
        language.inventory.set_symbols(["p", "t", "a"])
        ids = {p.symbol: p.id for p in language.inventory}
        loaded = self.round_trip(project).languages[0]
        self.assertEqual(loaded.id, language.id)
        self.assertEqual({p.symbol: p.id for p in loaded.inventory}, ids)

    def test_ids_are_unique(self):
        project = Project("Test Project")
        first = project.add_language("First")
        second = project.add_language("Second")
        first.inventory.set_symbols(["p", "a"])
        second.inventory.set_symbols(["p", "a"])
        ids = [first.id, second.id] + [p.id for p in first.inventory] + [p.id for p in second.inventory]
        self.assertEqual(len(ids), len(set(ids)))

    def test_set_symbols_keeps_ids(self):
        inventory = Project("Test Project").add_language("Test").inventory
        inventory.set_symbols(["p", "t", "a"])
        p_id = inventory.get("p").id
        inventory.set_symbols(["a", "p", "k"])
        self.assertEqual(inventory.get("p").id, p_id)
        self.assertNotIn("t", inventory)
        self.assertIn("k", inventory)

    def test_ids_are_never_reused(self):
        project = Project("Test Project")
        inventory = project.add_language("Test").inventory
        removed_id = inventory.add("t").id
        inventory.remove("t")
        # The removed Phoneme's ID was the newest one, so a reused ID would show up right after loading.
        loaded = self.round_trip(project)
        new_id = loaded.languages[0].inventory.add("t").id
        self.assertGreater(new_id, removed_id)

    def test_save_without_file(self):
        with self.assertRaises(ValueError):
            Project("Test Project").save()

    def test_save_to_loaded_file(self):
        project = self.round_trip(Project("Test Project"))
        project.add_language("Added")
        project.save()
        self.assertEqual(Project.load(self.file).languages[0].name, "Added")

    def test_load_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            Project.load(path.join(self.temp_dir.name, "missing.wwproj"))

    def test_load_not_a_project(self):
        with open(self.file, "wb") as f_out:
            f_out.write(b"just some text")
        with self.assertRaises(ProjectFileError):
            Project.load(self.file)

    def test_default_project(self):
        project = Project.load(DEFAULT_PROJECT)
        self.assertEqual(len(project.languages), 1)
        self.assertEqual(project.languages[0].inventory.symbols, STARTER_PHONEMES)

if __name__ == "__main__":
    unittest.main()

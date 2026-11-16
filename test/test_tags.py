# test/test_tags.py

import unittest
import tempfile

# Add the parent directory to the path so we can import the module we want to test
import sys
from os import path
sys.path.append(path.abspath(path.join(path.dirname(__file__), '../src')))

from wordweaver_project import Project

class TestTags(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file = path.join(self.temp_dir.name, "test.wwproj")
        self.project = Project("Test Project")
        self.proto = self.project.add_language("Proto")
        self.daughter = self.project.add_language("Daughter")

    def tearDown(self):
        self.temp_dir.cleanup()

    def round_trip(self) -> Project:
        self.project.save(self.file)
        return Project.load(self.file)

    def tag_names(self, project: Project, entry) -> list[str]:
        return [project.tags.get(tag_id).name for tag_id in entry.tag_ids]

    def test_round_trip_shared_by_two_languages(self):
        animals = self.project.tags.add("animals")
        sacred = self.project.tags.add("sacred words")
        self.project.tags.add("unused")
        wolf = self.proto.lexicon.add("ulka", ["wolf"])
        self.proto.lexicon.add("ta", ["one"])
        wulf = self.daughter.lexicon.add("ulf", ["wolf"])
        god = self.daughter.lexicon.add("deva", ["god"])
        self.proto.lexicon.tag(wolf, animals)
        self.proto.lexicon.tag(wolf, sacred)
        self.daughter.lexicon.tag(wulf, animals)
        self.daughter.lexicon.tag(god, sacred)
        loaded = self.round_trip()
        # The Tags come back with the same IDs and names, and each Entry points at the same ones.
        self.assertEqual([(t.id, t.name) for t in loaded.tags], [(t.id, t.name) for t in self.project.tags])
        for language, loaded_language in zip(self.project.languages, loaded.languages):
            self.assertEqual([(e.id, e.tag_ids) for e in loaded_language.lexicon], [(e.id, e.tag_ids) for e in language.lexicon])
        loaded_animals = loaded.tags.get(animals.id)
        self.assertEqual([e.glosses for e in loaded.tagged(loaded_animals)], [("wolf",), ("wolf",)])  # pyright: ignore[reportArgumentType]  None would fail the test anyway.
        self.assertEqual(self.tag_names(loaded, loaded.languages[0].lexicon.get(wolf.id)), ["animals", "sacred words"])

    def test_tags_take_ids_from_the_project_counter(self):
        entry = self.proto.lexicon.add("ta", ["one"])
        tag = self.project.tags.add("numbers")
        ids = [self.proto.id, self.daughter.id, entry.id] + [d.id for d in entry.definitions] + [tag.id]
        self.assertEqual(len(ids), len(set(ids)))

    def test_tag_ids_are_never_reused(self):
        tag = self.project.tags.add("old")
        self.project.tags.remove(tag)
        loaded = self.round_trip()
        self.assertNotEqual(loaded.tags.add("new").id, tag.id)

    def test_tag_and_untag(self):
        tag = self.project.tags.add("animals")
        entry = self.proto.lexicon.add("ulka", ["wolf"])
        self.proto.lexicon.tag(entry, tag)
        self.proto.lexicon.tag(entry, tag)
        self.assertEqual(entry.tag_ids, (tag.id,))
        self.proto.lexicon.untag(entry, tag)
        self.assertEqual(entry.tag_ids, ())
        self.assertEqual(self.round_trip().languages[0].lexicon.get(entry.id).tag_ids, ())

    def test_search_by_tag(self):
        animals = self.project.tags.add("animals")
        wolf = self.proto.lexicon.add("ulka", ["wolf"])
        self.proto.lexicon.add("ta", ["one"])
        bear = self.proto.lexicon.add("arka", ["bear"])
        self.proto.lexicon.tag(bear, animals)
        self.proto.lexicon.tag(wolf, animals)
        # Results come back in Lexicon order, not the order they were tagged.
        self.assertEqual(self.proto.lexicon.tagged(animals), [wolf, bear])
        self.assertEqual(self.daughter.lexicon.tagged(animals), [])

    def test_rename_shows_everywhere(self):
        tag = self.project.tags.add("animls")
        wolf = self.proto.lexicon.add("ulka", ["wolf"])
        wulf = self.daughter.lexicon.add("ulf", ["wolf"])
        self.proto.lexicon.tag(wolf, tag)
        self.daughter.lexicon.tag(wulf, tag)
        self.project.tags.rename(tag, "animals")
        loaded = self.round_trip()
        self.assertEqual(self.tag_names(loaded, loaded.languages[0].lexicon.get(wolf.id)), ["animals"])
        self.assertEqual(self.tag_names(loaded, loaded.languages[1].lexicon.get(wulf.id)), ["animals"])

    def test_remove_takes_tag_off_every_entry(self):
        animals = self.project.tags.add("animals")
        sacred = self.project.tags.add("sacred words")
        wolf = self.proto.lexicon.add("ulka", ["wolf"])
        wulf = self.daughter.lexicon.add("ulf", ["wolf"])
        self.proto.lexicon.tag(wolf, animals)
        self.proto.lexicon.tag(wolf, sacred)
        self.daughter.lexicon.tag(wulf, animals)
        self.project.tags.remove(animals)
        self.assertEqual(wolf.tag_ids, (sacred.id,))
        self.assertEqual(wulf.tag_ids, ())
        loaded = self.round_trip()
        self.assertEqual([t.name for t in loaded.tags], ["sacred words"])
        self.assertEqual(loaded.languages[0].lexicon.get(wolf.id).tag_ids, (sacred.id,))
        self.assertEqual(loaded.languages[1].lexicon.get(wulf.id).tag_ids, ())

    def test_names_must_be_unique_and_not_blank(self):
        tag = self.project.tags.add("animals")
        with self.assertRaises(ValueError):
            self.project.tags.add("  Animals ")
        with self.assertRaises(ValueError):
            self.project.tags.add("   ")
        other = self.project.tags.add("plants")
        with self.assertRaises(ValueError):
            self.project.tags.rename(other, "ANIMALS")
        # Renaming a Tag to its own name in a new case is fine.
        self.project.tags.rename(tag, "Animals")
        self.assertEqual(self.project.tags.find("animals"), tag)

    def test_tag_must_be_in_the_project(self):
        other_project = Project("Other")
        stranger = other_project.tags.add("animals")
        entry = self.proto.lexicon.add("ulka", ["wolf"])
        with self.assertRaises(KeyError):
            self.proto.lexicon.tag(entry, stranger)
        removed = self.project.tags.add("gone")
        self.project.tags.remove(removed)
        with self.assertRaises(KeyError):
            self.proto.lexicon.tag(entry, removed)
        with self.assertRaises(KeyError):
            self.project.tags.rename(removed, "back")

    def test_removing_an_entry_keeps_its_tags(self):
        tag = self.project.tags.add("animals")
        entry = self.proto.lexicon.add("ulka", ["wolf"])
        self.proto.lexicon.tag(entry, tag)
        self.proto.lexicon.remove(entry)
        loaded = self.round_trip()
        self.assertEqual([t.name for t in loaded.tags], ["animals"])
        self.assertEqual(loaded.tagged(loaded.tags.get(tag.id)), [])  # pyright: ignore[reportArgumentType]  None would fail the test anyway.

if __name__ == "__main__":
    unittest.main()

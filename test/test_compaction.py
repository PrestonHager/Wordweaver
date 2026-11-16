# test/test_compaction.py

import os
import unittest
import tempfile
from unittest import mock

# Add the parent directory to the path so we can import the module we want to test
import sys
from os import path
sys.path.append(path.abspath(path.join(path.dirname(__file__), '../src')))

from wordweaver_project import Project

def snapshot(project: Project) -> list:
    # Everything a user could see about the Project, in a form that's easy to compare.
    return [project.name, [(tag.id, tag.name) for tag in project.tags]] + [
        (
            language.id, language.name, language.kind,
            [(p.id, p.symbol) for p in language.inventory],
            [(c.id, c.name, c.symbols) for c in language.classes],
            [(r.id, str(r)) for r in language.allophone_rules],
            [(e.id, str(e.form), e.glosses, e.tag_ids) for e in language.lexicon],
        )
        for language in project.languages
    ]

class TestCompaction(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file = path.join(self.temp_dir.name, "test.wwproj")

    def tearDown(self):
        self.temp_dir.cleanup()

    def read_file(self) -> bytes:
        with open(self.file, "rb") as f_in:
            return f_in.read()

    def edited_project(self) -> Project:
        # Save a Project, then save a few rounds of edits to it as patches.
        project = Project("Test Project")
        # Pad the file out, so these patches stay under the size where saving compacts by itself.
        for _ in range(100):
            project.tags.add(os.urandom(16).hex())
        language = project.add_language("Test")
        language.inventory.set_symbols(["p", "t", "k", "a", "i"])
        project.save(self.file)
        self.base = self.read_file()
        vowel = language.get_class("Vowel")
        language.add_allophone_rule("t", "ɾ", before=vowel, after=vowel)
        project.save()
        animals = project.tags.add("animals")
        wolf = language.lexicon.add("pati", ["wolf"])
        language.lexicon.tag(wolf, animals)
        project.save()
        language.inventory.add("m")
        language.add_class("Nasals").add("m")
        language.lexicon.edit(wolf, glosses=["wolf", "dog"])
        project.save()
        return project

    def test_compact_by_hand(self):
        project = self.edited_project()
        self.assertTrue(self.read_file().startswith(self.base))
        patched_size = len(self.read_file())
        project.compact()
        self.assertLess(len(self.read_file()), patched_size)
        self.assertEqual(snapshot(Project.load(self.file)), snapshot(project))
        # A fresh save of the same Project is exactly what compaction should leave behind.
        fresh = path.join(self.temp_dir.name, "fresh.wwproj")
        project.save(fresh)
        with open(fresh, "rb") as f_in:
            self.assertEqual(self.read_file(), f_in.read())

    def test_saving_compacts_automatically(self):
        project = Project("Test Project")
        language = project.add_language("Test")
        language.inventory.set_symbols(["p", "t", "k", "a", "i"])
        for i in range(50):
            language.lexicon.add("pata", [f"gloss {i}"])
        project.save(self.file)
        base = self.read_file()
        compactions = 0
        for i in range(60):
            language.lexicon.add("tika", [f"new gloss {i}"])
            project.save()
            data = self.read_file()
            if data.startswith(base):
                # Still patching, so the patches have to stay at or under about a quarter of the file.
                self.assertLessEqual(len(data) - len(base), len(data) / 4, f"save {i}")
            else:
                # The file was rewritten, so it's the new base for the patches that follow.
                compactions += 1
                base = data
        self.assertGreater(compactions, 0)
        self.assertEqual(snapshot(Project.load(self.file)), snapshot(project))

    def test_one_small_patch_does_not_compact(self):
        project = Project("Test Project")
        language = project.add_language("Test")
        for i in range(50):
            language.lexicon.add("pata", [f"gloss {i}"])
        project.save(self.file)
        base = self.read_file()
        language.name = "Renamed"
        project.save()
        self.assertTrue(self.read_file().startswith(base))

    def test_crash_during_compaction_keeps_old_file(self):
        project = self.edited_project()
        before = self.read_file()
        # Fail the swap at the end of compaction, like the app crashing just before it.
        with mock.patch("os.replace", side_effect=OSError("crashed")):
            with self.assertRaises(OSError):
                project.compact()
        self.assertEqual(self.read_file(), before)
        self.assertEqual(snapshot(Project.load(self.file)), snapshot(project))

    def test_compact_without_file(self):
        with self.assertRaises(ValueError):
            Project("Test Project").compact()

if __name__ == "__main__":
    unittest.main()

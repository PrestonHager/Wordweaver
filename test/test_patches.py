# test/test_patches.py

import os
import unittest
import tempfile

# Add the parent directory to the path so we can import the module we want to test
import sys
from os import path
sys.path.append(path.abspath(path.join(path.dirname(__file__), '../src')))

from wordweaver_project import LanguageKind, Project

def snapshot(project: Project) -> list:
    # Everything a user could see about the Project, in a form that's easy to compare.
    return [project.name, [(tag.id, tag.name) for tag in project.tags]] + [
        (
            language.id, language.name, language.kind,
            [(p.id, p.symbol) for p in language.inventory],
            [(c.id, c.name, c.symbols) for c in language.classes],
            [(e.id, str(e.form), e.glosses, e.tag_ids) for e in language.lexicon],
        )
        for language in project.languages
    ]

def padded_project() -> Project:
    # Files compact once patches pass about a quarter of them, so these tests start from a file big enough to hold a few patches.
    project = Project("Test Project")
    for _ in range(60):
        project.tags.add(os.urandom(16).hex())
    return project

class TestPatches(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file = path.join(self.temp_dir.name, "test.wwproj")

    def tearDown(self):
        self.temp_dir.cleanup()

    def read_file(self) -> bytes:
        with open(self.file, "rb") as f_in:
            return f_in.read()

    def test_second_save_appends(self):
        project = padded_project()
        project.add_language("First").inventory.set_symbols(["p", "a"])
        project.save(self.file)
        first = self.read_file()
        project.add_language("Second")
        project.save()
        second = self.read_file()
        self.assertTrue(second.startswith(first))
        self.assertGreater(len(second), len(first))
        self.assertEqual(snapshot(Project.load(self.file)), snapshot(project))

    def test_edits_round_trip_through_patches(self):
        project = padded_project()
        first = project.add_language("First")
        first.inventory.set_symbols(["p", "t", "a"])
        second = project.add_language("Second", LanguageKind.DIALECT)
        project.save(self.file)
        base = self.read_file()
        # Now, rename things (replace), add Phonemes (insert), and remove them (delete).
        project.name = "Renamed Project"
        first.name = "Renamed"
        first.inventory.set_symbols(["p", "k", "a", "i"])
        project.remove_language(second)
        project.add_language("Third", LanguageKind.PROTO_LANGUAGE).inventory.set_symbols(["m"])
        project.save()
        self.assertTrue(self.read_file().startswith(base))
        self.assertEqual(snapshot(Project.load(self.file)), snapshot(project))

    def test_classes_lexicon_and_tags_round_trip_through_patches(self):
        project = padded_project()
        language = project.add_language("Test")
        language.inventory.set_symbols(["p", "t", "a", "i"])
        stops = language.add_class("Stops")
        stops.add("p")
        gone = language.add_class("Gone")
        animals = project.tags.add("animals")
        wolf = language.lexicon.add("pati", ["wolf"])
        removed = language.lexicon.add("ta", ["one"])
        project.save(self.file)
        base = self.read_file()
        # Now, edit, add, and remove a record in each table.
        stops.name = "Plosives"
        stops.add("t")
        language.remove_class(gone)
        language.add_class("Vowels Again").add("a")
        project.tags.rename(animals, "beasts")
        project.tags.add("numbers")
        language.lexicon.edit(wolf, form="pita", glosses=["wolf", "dog"])
        language.lexicon.tag(wolf, animals)
        language.lexicon.remove(removed)
        language.lexicon.add("ipa", ["eye"])
        project.save()
        self.assertTrue(self.read_file().startswith(base))
        self.assertEqual(snapshot(Project.load(self.file)), snapshot(project))

    def test_many_saves(self):
        project = padded_project()
        language = project.add_language("Test")
        project.save(self.file)
        for symbol in ["p", "t", "k", "a", "i", "u"]:
            language.inventory.add(symbol)
            project.save()
        language.inventory.remove("t")
        project.save()
        self.assertEqual(snapshot(Project.load(self.file)), snapshot(project))

    def test_saves_after_loading_a_patched_file(self):
        project = padded_project()
        project.add_language("First").inventory.set_symbols(["p", "a"])
        project.save(self.file)
        project.languages[0].inventory.add("t")
        project.save()
        # Load the patched file, then keep editing and saving it.
        loaded = Project.load(self.file)
        loaded.languages[0].name = "Edited after load"
        loaded.add_language("New after load").inventory.set_symbols(["ʃ"])
        loaded.save()
        self.assertEqual(snapshot(Project.load(self.file)), snapshot(loaded))

    def test_save_without_changes_writes_nothing(self):
        project = padded_project()
        project.add_language("Test")
        project.save(self.file)
        before = self.read_file()
        project.save()
        self.assertEqual(self.read_file(), before)

    def test_save_as_writes_whole_file(self):
        project = padded_project()
        project.add_language("Test").inventory.set_symbols(["p", "a"])
        project.save(self.file)
        project.languages[0].inventory.add("t")
        project.save()
        other = path.join(self.temp_dir.name, "other.wwproj")
        project.save(other)
        self.assertEqual(snapshot(Project.load(other)), snapshot(project))
        # A fresh file has no patches, so it's smaller than the one with a patch on the end.
        self.assertLess(path.getsize(other), path.getsize(self.file))

    def test_save_after_file_changed_elsewhere(self):
        project = padded_project()
        project.add_language("Mine")
        project.save(self.file)
        # Another Project gets saved over the same file, like a second window would.
        other = Project("Other Project")
        other.add_language("Theirs").inventory.set_symbols(["p", "t", "k", "a"])
        other.save(self.file)
        project.languages[0].inventory.add("m")
        project.save()
        self.assertEqual(snapshot(Project.load(self.file)), snapshot(project))

    def saved_twice(self) -> tuple[list, int]:
        # Save once, then save an edit as a patch, and return the first state and where the patch starts.
        project = padded_project()
        project.add_language("Test").inventory.set_symbols(["p", "a"])
        project.save(self.file)
        before = snapshot(project)
        patch_start = len(self.read_file())
        project.languages[0].inventory.add("t")
        project.add_language("Lost")
        project.save()
        return before, patch_start

    def write_file(self, data: bytes):
        with open(self.file, "wb") as f_out:
            f_out.write(data)

    def test_cut_off_patch_is_dropped(self):
        before, patch_start = self.saved_twice()
        data = self.read_file()
        # Cut the patch off at every point, as if the app crashed part way through writing it.
        for end in range(patch_start + 1, len(data)):
            self.write_file(data[:end])
            self.assertEqual(snapshot(Project.load(self.file)), before, f"cut at {end}")

    def test_bad_crc_patch_is_dropped(self):
        before, _ = self.saved_twice()
        data = bytearray(self.read_file())
        data[-1] ^= 0xFF
        self.write_file(bytes(data))
        self.assertEqual(snapshot(Project.load(self.file)), before)

    def test_save_after_dropped_patch(self):
        self.saved_twice()
        self.write_file(self.read_file()[:-2])
        # Saving over a broken patch has to rewrite the file, or the new patch would land after the broken one.
        project = Project.load(self.file)
        project.add_language("After")
        project.save()
        self.assertEqual(snapshot(Project.load(self.file)), snapshot(project))

if __name__ == "__main__":
    unittest.main()

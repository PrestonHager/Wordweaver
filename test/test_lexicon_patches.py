# test/test_lexicon_patches.py

import tempfile
import unittest
from pathlib import Path
from typing import Any

from google.protobuf.message_factory import GetMessageClass

# Add the parent directory to the path so we can import the module we want to test
import sys
from os import path
sys.path.append(path.abspath(path.join(path.dirname(__file__), '../src')))

from concepticon import ConceptList
from lexicon import ConceptReference, ConceptSource, Entry
from wordweaver_project import Language, Project
from wwformat import ChunkType, pb
from wwformat.container import decode_file
from wwformat.registry import record_class

CONCEPT_LIST = Path(__file__).parent / "fixtures" / "concept_list.json"

ENTRIES = ChunkType.ENTRIES
DEFINITIONS = ChunkType.DEFINITIONS
TAGS = ChunkType.TAGS

def snapshot(project: Project) -> list:
    # Everything a user could see about the Project and its Lexicons, in a form that's easy to compare.
    return [project.name, project.gloss_language, [(tag.id, tag.name) for tag in project.tags]] + [
        (
            language.id, language.name,
            [
                (entry.id, str(entry.form), entry.tag_ids, [
                    (d.id, d.glosses, d.terms, d.description, d.concept_reference) for d in entry.definitions
                ])
                for entry in language.lexicon
            ],
        )
        for language in project.languages
    ]

class Patch:
    """What one patch chunk changed: the record IDs it upserts and deletes in each table, and the single messages it replaces."""

    def __init__(self, message: Any, size: int):
        self.size = size
        self.upserts: dict[ChunkType, set[int]] = {}
        self.deletes: dict[ChunkType, set[int]] = {}
        for upsert in message.upserts:
            record = record_class(ChunkType(upsert.table))()
            record.ParseFromString(upsert.record)
            self.upserts.setdefault(ChunkType(upsert.table), set()).add(getattr(record, "id"))
        for delete in message.deletes:
            self.deletes.setdefault(ChunkType(delete.table), set()).add(delete.id)
        self.singles = {ChunkType(single.chunk_type) for single in message.singles}

def ids(*items) -> set[int]:
    return {item.id for item in items}

class TestLexiconPatches(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file = path.join(self.temp_dir.name, "test.wwproj")

    def tearDown(self):
        self.temp_dir.cleanup()

    def read_file(self) -> bytes:
        with open(self.file, "rb") as f_in:
            return f_in.read()

    def make_project(self, size: int=200) -> tuple[Project, Language, list[Entry]]:
        # Big enough that one patch stays well under the size where saving compacts the file.
        project = Project("Test Project")
        language = project.add_language("Test")
        language.inventory.set_symbols(["p", "t", "k", "a", "i", "u"])
        entries = [language.lexicon.add("pat" if i % 2 else "kiu", [f"gloss {i}"], description=f"word number {i}") for i in range(size)]
        project.save(self.file)
        return project, language, entries

    def save_patch(self, project: Project) -> Patch:
        # Save, check that it appended one patch chunk to the file, and say what that patch changed.
        before = self.read_file()
        project.save()
        after = self.read_file()
        self.assertTrue(after.startswith(before), "the save rewrote the file instead of appending a patch")
        chunks = decode_file(after).chunks
        self.assertEqual(chunks[-1].type_id, ChunkType.PATCH)
        # NOTE: the generated protobuf module has no type stubs, so we look the Patch message up by name.
        message = GetMessageClass(pb.DESCRIPTOR.message_types_by_name["Patch"])()
        message.ParseFromString(chunks[-1].payload)
        self.assertEqual(snapshot(Project.load(self.file)), snapshot(project))
        return Patch(message, len(after) - len(before))

    def test_one_edit_in_a_large_lexicon_appends_a_small_patch(self):
        project, language, entries = self.make_project(3000)
        full_size = len(self.read_file())
        entry = entries[1500]
        language.lexicon.edit(entry, form="tika", glosses=["changed"])
        patch = self.save_patch(project)
        self.assertEqual(patch.upserts, {ENTRIES: ids(entry), DEFINITIONS: ids(entry.definitions[0])})
        self.assertEqual(patch.deletes, {})
        # The whole Lexicon is tens of kilobytes, and the patch is only the one Entry and its Definition.
        self.assertGreater(full_size, 40000)
        self.assertLess(patch.size, 100)

    def test_many_saves_of_a_large_lexicon(self):
        project, language, entries = self.make_project(3000)
        lexicon = language.lexicon
        animals = project.tags.add("animals")
        for i, entry in enumerate(entries[:10]):
            lexicon.edit(entry, glosses=[f"edit {i}"])
            lexicon.tag(entry, animals)
            self.assertLess(self.save_patch(project).size, 200)
        lexicon.remove(entries[5])
        lexicon.add("tak", ["new"])
        self.save_patch(project)
        project.tags.remove(animals)
        self.save_patch(project)

    def test_add(self):
        project, language, _ = self.make_project()
        entry = language.lexicon.add("tiki", ["new"], terms=["NOUN"], description="a new word")
        patch = self.save_patch(project)
        self.assertEqual(patch.upserts, {ENTRIES: ids(entry), DEFINITIONS: ids(*entry.definitions)})
        self.assertEqual(patch.deletes, {})

    def test_edit_form(self):
        project, language, entries = self.make_project()
        language.lexicon.edit(entries[3], form="pupu")
        patch = self.save_patch(project)
        self.assertEqual(patch.upserts, {ENTRIES: ids(entries[3])})
        self.assertEqual(patch.deletes, {})

    def test_remove_deletes_its_definitions(self):
        project, language, entries = self.make_project()
        entry = entries[3]
        language.lexicon.add_definition(entry, ["other"])
        self.save_patch(project)
        definitions = list(entry.definitions)
        language.lexicon.remove(entry)
        patch = self.save_patch(project)
        self.assertEqual(patch.upserts, {})
        self.assertEqual(patch.deletes, {ENTRIES: ids(entry), DEFINITIONS: ids(*definitions)})

    def test_add_definition(self):
        project, language, entries = self.make_project()
        entry = entries[3]
        last = language.lexicon.add_definition(entry, ["last"])
        patch = self.save_patch(project)
        self.assertEqual(patch.upserts, {DEFINITIONS: ids(last)})
        # Adding at the front moves the others down, so they're saved again with their new positions.
        old = list(entry.definitions)
        first = language.lexicon.add_definition(entry, ["first"], index=0)
        patch = self.save_patch(project)
        self.assertEqual(patch.upserts, {DEFINITIONS: ids(first, *old)})
        self.assertEqual(patch.deletes, {})

    def test_edit_definition(self):
        project, language, entries = self.make_project()
        entry = entries[3]
        language.lexicon.add_definition(entry, ["second"])
        self.save_patch(project)
        second = entry.definitions[1]
        language.lexicon.edit_definition(entry, second, glosses=["two"], terms=["PL"], description="changed")
        patch = self.save_patch(project)
        self.assertEqual(patch.upserts, {DEFINITIONS: ids(second)})
        self.assertEqual(patch.deletes, {})

    def test_remove_definition(self):
        project, language, entries = self.make_project()
        entry = entries[3]
        lexicon = language.lexicon
        lexicon.add_definition(entry, ["second"])
        lexicon.add_definition(entry, ["third"])
        self.save_patch(project)
        first, second, third = entry.definitions
        # Removing the last one leaves the others where they were.
        lexicon.remove_definition(entry, third)
        patch = self.save_patch(project)
        self.assertEqual(patch.upserts, {})
        self.assertEqual(patch.deletes, {DEFINITIONS: ids(third)})
        # Removing the first one moves the second up.
        lexicon.remove_definition(entry, first)
        patch = self.save_patch(project)
        self.assertEqual(patch.upserts, {DEFINITIONS: ids(second)})
        self.assertEqual(patch.deletes, {DEFINITIONS: ids(first)})

    def test_move_definition(self):
        project, language, entries = self.make_project()
        entry = entries[3]
        lexicon = language.lexicon
        lexicon.add_definition(entry, ["second"])
        lexicon.add_definition(entry, ["third"])
        lexicon.add_definition(entry, ["fourth"])
        self.save_patch(project)
        first, second, third, fourth = entry.definitions
        # Moving the third to the front shifts the first and second down, and the fourth stays put.
        lexicon.move_definition(entry, third, 0)
        patch = self.save_patch(project)
        self.assertEqual(patch.upserts, {DEFINITIONS: ids(first, second, third)})
        self.assertEqual(patch.deletes, {})
        self.assertEqual(entry.definitions, [third, first, second, fourth])

    def test_tag_and_untag(self):
        project, language, entries = self.make_project()
        animals = project.tags.add("animals")
        self.save_patch(project)
        language.lexicon.tag(entries[3], animals)
        patch = self.save_patch(project)
        self.assertEqual(patch.upserts, {ENTRIES: ids(entries[3])})
        language.lexicon.untag(entries[3], animals)
        patch = self.save_patch(project)
        self.assertEqual(patch.upserts, {ENTRIES: ids(entries[3])})
        self.assertEqual(patch.deletes, {})

    def test_add_and_rename_tag(self):
        project, language, entries = self.make_project()
        animals = project.tags.add("animals")
        patch = self.save_patch(project)
        self.assertEqual(patch.upserts, {TAGS: ids(animals)})
        language.lexicon.tag(entries[3], animals)
        self.save_patch(project)
        # Entries only keep the Tag's ID, so renaming it doesn't touch them.
        project.tags.rename(animals, "beasts")
        patch = self.save_patch(project)
        self.assertEqual(patch.upserts, {TAGS: ids(animals)})
        self.assertEqual(patch.deletes, {})

    def test_remove_tag_rewrites_its_entries(self):
        project, language, entries = self.make_project()
        other = project.add_language("Other")
        animals = project.tags.add("animals")
        sacred = project.tags.add("sacred")
        wolf = other.lexicon.add("ulf", ["wolf"])
        language.lexicon.tag(entries[3], animals)
        language.lexicon.tag(entries[7], animals)
        other.lexicon.tag(wolf, animals)
        language.lexicon.tag(entries[9], sacred)
        self.save_patch(project)
        project.tags.remove(animals)
        patch = self.save_patch(project)
        self.assertEqual(patch.upserts, {ENTRIES: ids(entries[3], entries[7], wolf)})
        self.assertEqual(patch.deletes, {TAGS: ids(animals)})

    def test_set_and_clear_concept_reference(self):
        project, language, entries = self.make_project()
        entry = entries[3]
        definition = entry.definitions[0]
        language.lexicon.set_concept_reference(entry, definition, ConceptReference(ConceptSource.OPEN_ENGLISH_WORDNET, "oewn-02084071-n"))
        patch = self.save_patch(project)
        self.assertEqual(patch.upserts, {DEFINITIONS: ids(definition)})
        language.lexicon.clear_concept_reference(entry, definition)
        patch = self.save_patch(project)
        self.assertEqual(patch.upserts, {DEFINITIONS: ids(definition)})
        self.assertEqual(patch.deletes, {})

    def test_seed_from_concept_list(self):
        project, language, _ = self.make_project()
        added = language.lexicon.seed_from_concept_list(ConceptList.load(CONCEPT_LIST))
        self.assertTrue(added)
        patch = self.save_patch(project)
        self.assertEqual(patch.upserts, {ENTRIES: ids(*added), DEFINITIONS: {d.id for entry in added for d in entry.definitions}})
        self.assertEqual(patch.deletes, {})

    def test_gloss_language(self):
        project, _, _ = self.make_project()
        project.gloss_language = "fr"
        patch = self.save_patch(project)
        self.assertEqual(patch.singles, {ChunkType.PROJECT})
        self.assertEqual(patch.upserts, {})
        self.assertEqual(patch.deletes, {})

    def test_compaction_gives_the_same_project(self):
        project, language, entries = self.make_project()
        lexicon = language.lexicon
        animals = project.tags.add("animals")
        lexicon.tag(entries[0], animals)
        self.save_patch(project)
        lexicon.add_definition(entries[0], ["second"], index=0)
        lexicon.remove(entries[1])
        self.save_patch(project)
        project.tags.rename(animals, "beasts")
        lexicon.edit(entries[2], form="tuk")
        self.save_patch(project)
        before = snapshot(project)
        patched_size = len(self.read_file())
        project.compact()
        self.assertLess(len(self.read_file()), patched_size)
        self.assertEqual(snapshot(Project.load(self.file)), before)
        # A fresh save of the same Project is exactly what compaction should leave behind.
        fresh = path.join(self.temp_dir.name, "fresh.wwproj")
        project.save(fresh)
        with open(fresh, "rb") as f_in:
            self.assertEqual(self.read_file(), f_in.read())

if __name__ == "__main__":
    unittest.main()

# test/test_entry_editor.py

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

# Run Qt without a screen, so this works in CI.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QDialog

from entry_editor import EntryEditor, HomophoneWarning
from wordweaver_project import Project

app = QApplication.instance() or QApplication([])

class TestEntryEditorFormCheck(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.file = os.path.join(self.temp_dir.name, "test.wwproj")
        self.project = Project("Test Project")
        self.language = self.project.add_language("Testish")
        self.language.inventory.set_symbols(["t", "a", "i"])
        self.tag = self.project.tags.add("animals")

    def tearDown(self):
        self.temp_dir.cleanup()

    def editor(self, form: str, gloss: str="dog", entry=None) -> EntryEditor:
        editor = EntryEditor(self.language, entry)
        editor.form_input.setText(form)
        editor.glosses_input.setPlainText(gloss)
        return editor

    def test_form_in_inventory_shows_no_warning(self):
        editor = self.editor("tati")
        self.assertFalse(editor.form_warnings.isVisibleTo(editor))
        self.assertEqual(editor.form_warnings.add_buttons, {})

    def test_unknown_phoneme_is_flagged_as_you_type(self):
        editor = self.editor("ta")
        editor.form_input.setText("taki")
        self.assertTrue(editor.form_warnings.isVisibleTo(editor))
        self.assertEqual(list(editor.form_warnings.add_buttons), ["k"])

    def test_add_to_inventory_clears_the_flag_and_round_trips(self):
        editor = self.editor("kati")
        editor.form_warnings.add_buttons["k"].click()
        self.assertIn("k", self.language.inventory)
        self.assertEqual(editor.added_phonemes, ["k"])
        self.assertFalse(editor.form_warnings.isVisibleTo(editor))
        editor.accept()
        self.assertEqual(editor.result(), QDialog.DialogCode.Accepted)
        # The new Phoneme and the Entry both come back after a save and load.
        self.project.save(self.file)
        loaded = Project.load(self.file).languages[0]
        self.assertEqual(loaded.inventory.get("k"), self.language.inventory.get("k"))
        self.assertEqual(str(loaded.lexicon.get(editor.entry.id).form), "kati")

    def test_invalid_ipa_is_reported_and_cant_be_added(self):
        editor = self.editor("taː")
        self.assertTrue(editor.form_warnings.isVisibleTo(editor))
        self.assertEqual(editor.form_warnings.check.invalid, ("ː",))
        self.assertEqual(editor.form_warnings.add_buttons, {})

    def test_warnings_never_block_saving(self):
        editor = self.editor("kaː")
        editor.accept()
        self.assertEqual(editor.result(), QDialog.DialogCode.Accepted)
        self.assertEqual(str(editor.entry.form), "kaː")
        self.assertNotIn("k", self.language.inventory)

    def test_editing_an_entry_checks_its_form(self):
        entry = self.language.lexicon.add("kat", ["cat"])
        editor = EntryEditor(self.language, entry)
        self.assertEqual(list(editor.form_warnings.add_buttons), ["k"])

    def test_homophone_check_and_tags_still_work(self):
        self.language.lexicon.add("tata", ["father"])
        editor = self.editor("tata", "dad")
        editor.tag_picker.tag_list.item(0).setCheckState(Qt.CheckState.Checked)
        # The Homophone warning still comes up, and saving anyway keeps the Tag.
        with mock.patch.object(HomophoneWarning, "exec", return_value=QDialog.DialogCode.Accepted) as warning:
            editor.accept()
        warning.assert_called_once()
        self.assertEqual(editor.entry.tag_ids, (self.tag.id,))
        self.assertEqual(len(self.language.lexicon.homophones_of("tata")), 2)

if __name__ == "__main__":
    unittest.main()

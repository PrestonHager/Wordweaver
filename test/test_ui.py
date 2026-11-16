import os
import sys
import unittest
from pathlib import Path

# Run Qt without a screen, so this works in CI.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from PyQt6.QtWidgets import QApplication

from main import App
from phonotactics import SyllablePart
from theme import theme
from wordweaver_project import Project

app = QApplication.instance() or QApplication([])

class TestApp(unittest.TestCase):
    def setUp(self):
        # Use a fixed mode so the test doesn't read or write the saved theme.
        theme.mode = "light"
        theme.apply(app)
        self.project = Project("Test Project")
        self.language = self.project.add_language("Testish")
        self.language.inventory.set_symbols(["p", "a"])
        self.window = App(self.project)

    def tearDown(self):
        self.window.project = None
        self.window.deleteLater()

    def test_welcome_without_project(self):
        window = App(None)
        self.assertIs(window.root.currentWidget(), window.welcome)
        self.assertFalse(window.menu_actions["save"].isEnabled())
        window.deleteLater()

    def test_workspace_with_project(self):
        self.assertIs(self.window.root.currentWidget(), self.window.workspace)
        self.assertIs(self.window.pages.currentWidget(), self.window.overview_page)
        self.assertEqual(self.window.language_picker.currentText(), "Testish")

    def test_chart_toggles_inventory(self):
        page = self.window.phonology_page
        self.assertTrue(page.buttons["p"].isChecked())
        # Clicking a chart button adds the sound, and clicking again removes it.
        page.buttons["t"].click()
        self.assertIn("t", self.language.inventory)
        page.buttons["t"].click()
        self.assertNotIn("t", self.language.inventory)
        self.assertEqual(page.count.text(), "2")

    def test_typed_symbol(self):
        page = self.window.phonology_page
        # A mark that isn't a sound shows an error and can't be added.
        page.symbol_input.setText("ʰ")
        self.assertTrue(page.error.isVisibleTo(page))  # pyright: ignore[reportArgumentType]  PyQt6 stub bug, see pyproject.
        self.assertFalse(page.add_button.isEnabled())
        page.add_symbol()
        self.assertNotIn("ʰ", self.language.inventory)
        # An off-chart sound is added.
        page.symbol_input.setText("ǀ")
        page.add_symbol()
        self.assertIn("ǀ", self.language.inventory)
        self.assertEqual(page.symbol_input.text(), "")

    def test_chip_removes_phoneme(self):
        page = self.window.phonology_page
        chip = page.chips.itemAt(0).widget()
        chip.removed.emit(chip.text)
        self.assertNotIn("p", self.language.inventory)
        self.assertFalse(page.buttons["p"].isChecked())

    def test_card_opens_phonology_for_its_language(self):
        other = self.project.add_language("Other")
        self.window._update_project_view()
        self.window.overview_page.phonology_requested.emit(other)
        self.assertIs(self.window.language, other)
        self.assertIs(self.window.pages.currentWidget(), self.window.phonology_page)
        self.assertTrue(self.window.nav_buttons["phonology"].isChecked())

    def test_lexicon_inventory_change_redraws_phonology(self):
        # A Phoneme added from the Entry editor shows up on the chart without switching Language.
        self.language.inventory.add("t")
        self.window.lexicon_page.inventory_changed.emit()
        self.assertTrue(self.window.phonology_page.buttons["t"].isChecked())
        self.assertEqual(self.window.phonology_page.count.text(), "3")

    def test_dark_theme_applies(self):
        theme.mode = "dark"
        theme.apply(app)
        self.assertTrue(theme.is_dark)
        self.assertEqual(self.window.theme_button.toolTip(), "Switch to light mode")

    def test_phonotactics_page_builds_and_checks(self):
        self.window.nav_buttons["phonotactics"].click()
        page = self.window.phonotactics_page
        self.assertIs(self.window.pages.currentWidget(), page)
        card = page.structures_card
        # First, build (C)V(C) with the label buttons, then add it.
        buttons = {card.labels.itemAt(i).widget().text(): card.labels.itemAt(i).widget() for i in range(card.labels.count())}
        self.assertTrue({"C", "V", "N", "S"} <= buttons.keys())
        card.optional.setChecked(True)
        buttons["C"].click()
        card.optional.setChecked(False)
        buttons["V"].click()
        card.optional.setChecked(True)
        buttons["C"].click()
        self.assertEqual(card.notation_input.text(), "(C)V(C)")
        self.assertEqual(card.preview.parts, {SyllablePart.ONSET: ["(C)"], SyllablePart.NUCLEUS: ["V"], SyllablePart.CODA: ["(C)"]})
        card.add_button.click()
        self.assertEqual([s.notation for s in self.language.phonotactics.syllable_structures], ["(C)V(C)"])
        self.assertEqual(card.count.text(), "1")
        # Then check a Form that fits and one that doesn't.
        page.check_card.form_input.setText("papa")
        self.assertEqual(page.check_card.syllables.text(), "/pa.pa/")
        page.check_card.form_input.setText("ppa")
        self.assertIn("can't be split", page.check_card.result.text())
        # A bad structure shows an error and isn't added.
        card.notation_input.setText("CC")
        card.add_structure()
        self.assertTrue(card.error.isVisibleTo(card))  # pyright: ignore[reportArgumentType]  PyQt6 stub bug.
        self.assertEqual(len(self.language.phonotactics.syllable_structures), 1)

    def test_class_label_from_classes_card(self):
        card = self.window.phonology_page.classes_card
        stop = self.language.get_class("Stop")
        card.selected = stop
        card.refresh()
        card.label_input.setText("P")
        card.rename()
        self.assertEqual(stop.label, "P")
        # A label that's taken leaves both the name and label as they were.
        card.name_input.setText("Plosive")
        card.label_input.setText("V")
        card.rename()
        self.assertEqual((stop.name, stop.label), ("Stop", "P"))
        self.assertTrue(card.error.isVisibleTo(card))  # pyright: ignore[reportArgumentType]  PyQt6 stub bug.

if __name__ == "__main__":
    unittest.main()

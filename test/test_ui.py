import os
import sys
import unittest
from pathlib import Path

# Run Qt without a screen, so this works in CI.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from PyQt6.QtWidgets import QApplication

from main import App
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

if __name__ == "__main__":
    unittest.main()

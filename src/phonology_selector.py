# phonology_selector.py

from ipapy import IPA_TO_UNICODE
from PyQt6.QtWidgets import (
        QApplication, QPushButton, QGridLayout, QHBoxLayout, QLabel,
        QMainWindow, QTextEdit, QVBoxLayout, QWidget
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

import logging

from phonology_const import PULMONIC_CONSONANTS, VOWELS
from wordweaver_project import WordweaverProject

SELECTOR_TEXT = """Instructions: Select the phonemes to include below. \
A preview of the selected consonants can be found at the bottom. \
When finished, click Save & Close."""

CONSONANT_MANNERS = ["nasal", "plosive", "trill", "tap", "fricative",
                     "lateral-fricative", "approximant", "lateral-approximant"]
CONSONANT_PLACES = ["bi-labial", "labio-dental", "dental", "alveolar",
                    "post-alveolar", "retroflex", "palatal", "velar", "uvular",
                    "pharyngeal", "glottal"]
VOWEL_MANNERS = ["close", "near-close", "close-mid", "mid", "open-mid",
                 "near-open", "open"]
VOWEL_PLACES = ["front", "central", "back"]


class PhonologySelector(QMainWindow):
    def __init__(self, project: WordweaverProject = None):
        super().__init__()

        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)

        # Setup defaults for the class
        self._project = project
        # The inventories are stored as str lists until the project property is called
        self.pulmonic_inventory = []
        self.vowel_inventory = []
        if self._project is not None:
            self.pulmonic_inventory = [IPA_TO_UNICODE[p.canonical_representation]
                                       for p in self._project.pulmonic_inventory]
            self.vowel_inventory = [IPA_TO_UNICODE[v.canonical_representation]
                                    for v in self._project.vowel_inventory]

        # Construct GUI
        self.logger.debug("Constructing PhonologySelector GUI")
        self.setWindowTitle("Phonology Selector")

        self.setGeometry(100, 100, 640, 480)

        widget = QWidget(self)
        self.setCentralWidget(widget)
        self.layout = QVBoxLayout(widget)

        # Add text and header
        header = QLabel("Phonology Selector", self)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        header.setContentsMargins(0, 0, 0, 20)
        self.layout.addWidget(header)
        text = QLabel(SELECTOR_TEXT, self)
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text.setContentsMargins(20, 0, 0, 20)
        text.setWordWrap(True)
        self.layout.addWidget(text)

        # Create an grid layout; right for the table, left for vowels
        self.content = QWidget(self)
        self.content_layout = QGridLayout(self.content)
        self.layout.addWidget(self.content)

        # Generate table of phonemes
        table_widget = QWidget(self.content)
        self.content_layout.addWidget(table_widget, 0, 0)
        self.pulmonic_layout = QGridLayout(table_widget)

        # Add the selection preview
        selection_group = QWidget(self.content)
        selection_group_layout = QHBoxLayout(selection_group)

        selection_label = QLabel("Selected:", self)
        selection_group_layout.addWidget(selection_label)
        self.selection = QTextEdit(', '.join(self.pulmonic_inventory), selection_group)
        self.selection.setMaximumHeight(50)
        self.selection.textChanged.connect(self.update_pulmonic_selection)
        selection_group_layout.addWidget(self.selection)
        self.content_layout.addWidget(selection_group, 1, 0)

        # Add the vowel selection table
        vowel_group = QWidget(self.content)
        self.vowel_layout = QGridLayout(vowel_group)
        self.content_layout.addWidget(vowel_group, 0, 1)

        # Add the vowel selection preview
        vowel_selection_group = QWidget(vowel_group)
        vowel_selection_group_layout = QHBoxLayout(vowel_selection_group)

        vowel_selection_label = QLabel("Selected:", vowel_group)
        vowel_selection_group_layout.addWidget(vowel_selection_label)
        self.vowel_selection = QTextEdit(', '.join(self.vowel_inventory), vowel_group)
        self.vowel_selection.setMaximumHeight(50)
        self.vowel_selection.textChanged.connect(self.update_vowel_selection)
        vowel_selection_group_layout.addWidget(self.vowel_selection)
        self.content_layout.addWidget(vowel_selection_group, 1, 1)

        # Add the save buttons
        buttons = QWidget(self)
        buttons_layout = QHBoxLayout(buttons)

        cancel_button = QPushButton("Cancel", buttons)
        cancel_button.clicked.connect(self.close)
        buttons_layout.addWidget(cancel_button)

        save_button = QPushButton("Save && Close", buttons)
        save_button.clicked.connect(self.save)
        buttons_layout.addWidget(save_button)

        self.layout.addWidget(buttons)

        self._add_phonology_const()
        self._add_phonology_vowels()

    def _add_phonology_const(self):
        self.logger.debug("Adding phonology consonant buttons to PhonologySelector")
        self._add_consonant_labels()
        self._add_consonant_buttons()

    def _add_consonant_labels(self):
        """Add row and column labels for the consonant table."""
        for i in range(len(CONSONANT_MANNERS)):
            manner = CONSONANT_MANNERS[i]
            label = QLabel(manner, self)
            self.pulmonic_layout.addWidget(label, i+1, 0)
        for j in range(len(CONSONANT_PLACES)):
            place = CONSONANT_PLACES[j]
            label = QLabel(place, self)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.pulmonic_layout.addWidget(label, 0, j+1)

    def _add_consonant_buttons(self):
        """Add consonant phoneme buttons to the table."""
        for i in range(len(CONSONANT_MANNERS)):
            manner = CONSONANT_MANNERS[i]
            for j in range(len(CONSONANT_PLACES)):
                place = CONSONANT_PLACES[j]
                try:
                    phonemes = PULMONIC_CONSONANTS[manner][place]
                    button_group = self._create_consonant_button_group(phonemes)
                    self.pulmonic_layout.addWidget(button_group, i+1, j+1)
                except KeyError:
                    pass

    def _create_consonant_button_group(self, phonemes):
        """Create a button group widget for consonant phonemes."""
        button_group = QWidget()
        button_layout = QHBoxLayout(button_group)

        if "voiced" in phonemes:
            self._add_consonant_button(button_layout, phonemes["voiced"])
        else:
            button_layout.addStretch()

        if "voiceless" in phonemes:
            self._add_consonant_button(button_layout, phonemes["voiceless"])
        else:
            button_layout.addStretch()

        return button_group

    def _add_consonant_button(self, button_layout, phoneme):
        """Add a single consonant button to the layout."""
        button = QPushButton(phoneme)
        button.setProperty("phoneme", phoneme)
        button.setMinimumHeight(25)
        button.setMaximumWidth(20)
        button.setCheckable(True)
        button.setChecked(phoneme in self.pulmonic_inventory)
        button.clicked.connect(self._on_pulmonic_button_clicked)
        button_layout.addWidget(button)

    def _add_phonology_vowels(self):
        self.logger.debug("Adding phonology vowel buttons to PhonologySelector")
        self._add_vowel_labels()
        self._add_vowel_buttons()

    def _add_vowel_labels(self):
        """Add row and column labels for the vowel table."""
        for i in range(len(VOWEL_MANNERS)):
            manner = VOWEL_MANNERS[i]
            label = QLabel(manner, self)
            self.vowel_layout.addWidget(label, i+1, 0)
        for j in range(len(VOWEL_PLACES)):
            place = VOWEL_PLACES[j]
            label = QLabel(place, self)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.vowel_layout.addWidget(label, 0, j+1)

    def _add_vowel_buttons(self):
        """Add vowel phoneme buttons to the table."""
        num_manners = len(VOWEL_MANNERS)
        num_places = len(VOWEL_PLACES)
        for i in range(num_manners):
            manner = VOWEL_MANNERS[i]
            for j in range(num_places):
                place = VOWEL_PLACES[j]
                try:
                    phonemes = VOWELS[manner][place]
                    button_group = self._create_vowel_button_group(phonemes, i, j, num_manners, num_places)
                    self._add_vowel_button_group_to_layout(button_group, i, j, num_places)
                except KeyError:
                    pass

    def _create_vowel_button_group(self, phonemes, row_idx, col_idx, num_manners, num_places):
        """Create a button group widget for vowel phonemes."""
        button_group = QWidget()
        button_layout = QHBoxLayout(button_group)

        if "unrounded" in phonemes:
            self._add_vowel_button(button_layout, phonemes["unrounded"])
        if "rounded" in phonemes:
            self._add_vowel_button(button_layout, phonemes["rounded"])

        self._set_vowel_button_margins(button_layout, row_idx, col_idx, num_manners)
        return button_group

    def _add_vowel_button(self, button_layout, phoneme):
        """Add a single vowel button to the layout."""
        button = QPushButton(phoneme)
        button.setProperty("phoneme", phoneme)
        button.setMinimumHeight(25)
        button.setMaximumWidth(20)
        button.setCheckable(True)
        button.setChecked(phoneme in self.vowel_inventory)
        button.clicked.connect(self._on_vowel_button_clicked)
        button_layout.addWidget(button)

    def _set_vowel_button_margins(self, button_layout, row_idx, col_idx, num_manners):
        """Set margins for vowel buttons based on position."""
        if col_idx == 0:
            button_layout.setContentsMargins(20*row_idx, 0, 20*(num_manners-row_idx), 0)
        elif col_idx == 1:
            button_layout.setContentsMargins(12*row_idx, 0, 12*(num_manners-row_idx), 0)

    def _add_vowel_button_group_to_layout(self, button_group, row_idx, col_idx, num_places):
        """Add the button group to the vowel layout."""
        if col_idx >= num_places - 1:
            self.vowel_layout.addWidget(button_group, row_idx+1, col_idx+1, 1, 2)
        else:
            self.vowel_layout.addWidget(button_group, row_idx+1, col_idx+1)

    def _on_pulmonic_button_clicked(self, checked):
        button = self.sender()
        phoneme = button.property("phoneme")
        self.logger.debug(f"Pulmonic phoneme `{phoneme}` is now {'selected' if checked else 'deselected'}")
        if checked:
            self.pulmonic_inventory.append(phoneme)
        else:
            self.pulmonic_inventory.remove(phoneme)
        # Update the text box
        self.selection.setText(', '.join(self.pulmonic_inventory))

    def _on_vowel_button_clicked(self, checked):
        button = self.sender()
        phoneme = button.property("phoneme")
        self.logger.debug(f"Vowel phoneme `{phoneme}` is now {'selected' if checked else 'deselected'}")
        if checked:
            self.vowel_inventory.append(phoneme)
        else:
            self.vowel_inventory.remove(phoneme)
        # Update the text box
        self.vowel_selection.setText(', '.join(self.vowel_inventory))

    def update_pulmonic_selection(self):
        self.logger.debug("Updating phonology inventory from selection text box")
        self.pulmonic_inventory = [c.strip() for c in self.selection.toPlainText().split(",")]
        for i in range(1, self.pulmonic_layout.rowCount()):
            for j in range(1, self.pulmonic_layout.columnCount()):
                item = self.pulmonic_layout.itemAtPosition(i, j)
                if item is not None:
                    for k in range(self.pulmonic_layout.itemAtPosition(i, j).widget().layout().count()):
                        button = item.widget().layout().itemAt(k).widget()
                        if button is not None:
                            phoneme = button.property("phoneme")
                            button.setChecked(phoneme in self.pulmonic_inventory)

    def update_vowel_selection(self):
        self.logger.debug("Updating vowel inventory from selection text box")
        self.vowel_inventory = [v.strip() for v in self.vowel_selection.toPlainText().split(",")]
        for i in range(1, self.vowel_layout.rowCount()):
            for j in range(1, self.vowel_layout.columnCount()):
                item = self.vowel_layout.itemAtPosition(i, j)
                if item is not None:
                    for k in range(self.vowel_layout.itemAtPosition(i, j).widget().layout().count()):
                        button = item.widget().layout().itemAt(k).widget()
                        if button is not None:
                            phoneme = button.property("phoneme")
                            button.setChecked(phoneme in self.vowel_inventory)

    @property
    def project(self):
        # Update the project with the new phonology inventory
        if self._project is not None:
            self._project.pulmonic_inventory = self.pulmonic_inventory
            self._project.vowel_inventory = self.vowel_inventory
        return self._project

    def save(self):
        self.close()


if __name__ == "__main__":
    logging.basicConfig(filename="phonology_selector.log",
                        level=logging.DEBUG,
                        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    app = QApplication([])
    window = PhonologySelector()
    window.show()
    app.exec()

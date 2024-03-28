# phonology_selector.py

from ipapy import IPA_TO_UNICODE
from PyQt6.QtWidgets import QApplication, QPushButton, QGridLayout, QHBoxLayout, QLabel, QMainWindow, QTextEdit, QVBoxLayout, QWidget
from PyQt6.QtGui import QFont, QPalette
from PyQt6.QtCore import Qt

import logging

from phonology_const import PULMONIC_CONSONANTS, VOWELS
from wordweaver_project import WordweaverProject

class PhonologySelector(QMainWindow):
    def __init__(self, project: WordweaverProject=None):
        super().__init__()

        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)

        # Setup defaults for the class
        self._project = project
        # The inventories are stored as str lists until the project property is called
        self.pulmonic_inventory = [IPA_TO_UNICODE[p.canonical_representation] for p in self._project.pulmonic_inventory] if self._project is not None else []
        self.vowel_inventory = [IPA_TO_UNICODE[v.canonical_representation] for v in self._project.vowel_inventory] if self._project is not None else []

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
        text = QLabel("Instructions: Select the phonemes to include below. A preview of the selected consonants can be found at the bottom. When finished, click Save & Close.", self)
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

    def _add_phonology_const(self):
        self.logger.debug("Adding phonology consonant buttons to PhonologySelector")
        # Add the pulmonic consonants labels
        manners = ["nasal", "plosive", "trill", "tap", "fricative", "lateral-fricative", "approximant", "lateral-approximant"]
        places = ["bi-labial", "labio-dental", "dental", "alveolar", "post-alveolar", "retroflex", "palatal", "velar", "uvular", "pharyngeal", "glottal"]
        for i in range(len(manners)):
            manner = manners[i]
            label = QLabel(manner, self)
            self.pulmonic_layout.addWidget(label, i+1, 0)
        for j in range(len(places)):
            place = places[j]
            label = QLabel(place, self)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.pulmonic_layout.addWidget(label, 0, j+1)
        
        # Add the vowels labels
        vowel_manners = ["close", "near-close", "close-mid", "mid", "open-mid", "near-open", "open"]
        vowel_places = ["front", "central", "back"]
        for i in range(len(vowel_manners)):
            manner = vowel_manners[i]
            label = QLabel(manner, self)
            self.vowel_layout.addWidget(label, i+1, 0)
        for j in range(len(vowel_places)):
            place = vowel_places[j]
            label = QLabel(place, self)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.vowel_layout.addWidget(label, 0, j+1)

        # Add the pulmonic consonant symbols
        for i in range(len(manners)):
            manner = manners[i]
            for j in range(len(places)):
                place = places[j]
                try:
                    phonemes = PULMONIC_CONSONANTS[manner][place]
                    button_group = QWidget()
                    button_layout = QHBoxLayout(button_group)
                    # Create a button for each voiced/voiceless pair
                    if "voiced" in phonemes:
                        button_voiced = QPushButton(phonemes["voiced"])
                        button_voiced.setProperty("phoneme", phonemes["voiced"])
                        button_voiced.setMinimumHeight(25)
                        button_voiced.setMaximumWidth(20)
                        button_voiced.setCheckable(True)
                        button_voiced.setChecked(phonemes["voiced"] in self.pulmonic_inventory)
                        button_voiced.clicked.connect(self._on_pulmonic_button_clicked)
                        button_layout.addWidget(button_voiced)
                    else:
                        button_layout.addStretch()
                    if "voiceless" in phonemes:
                        button_voiceless = QPushButton(phonemes["voiceless"])
                        button_voiceless.setProperty("phoneme", phonemes["voiceless"])
                        button_voiceless.setMinimumHeight(25)
                        button_voiceless.setMaximumWidth(20)
                        button_voiceless.setCheckable(True)
                        button_voiceless.setChecked(phonemes["voiceless"] in self.pulmonic_inventory)
                        button_voiceless.clicked.connect(self._on_pulmonic_button_clicked)
                        button_layout.addWidget(button_voiceless)
                    else:
                        button_layout.addStretch()
                    self.pulmonic_layout.addWidget(button_group, i+1, j+1)
                except KeyError:
                    pass
        
        # Add the vowel symbols
        I = len(vowel_manners)
        J = len(vowel_places)
        for i in range(I):
            manner = vowel_manners[i]
            for j in range(J):
                place = vowel_places[j]
                try:
                    phonemes = VOWELS[manner][place]
                    button_group = QWidget()
                    button_layout = QHBoxLayout(button_group)
                    if "unrounded" in phonemes:
                        phoneme = phonemes["unrounded"]
                        button_rounded = QPushButton(phoneme)
                        button_rounded.setProperty("phoneme", phoneme)
                        button_rounded.setMinimumHeight(25)
                        button_rounded.setMaximumWidth(20)
                        button_rounded.setCheckable(True)
                        button_rounded.setChecked(phoneme in self.vowel_inventory)
                        button_rounded.clicked.connect(self._on_vowel_button_clicked)
                        button_layout.addWidget(button_rounded)
                    if "rounded" in phonemes:
                        phoneme = phonemes["rounded"]
                        button_unrounded = QPushButton(phoneme)
                        button_unrounded.setProperty("phoneme", phoneme)
                        button_unrounded.setMinimumHeight(25)
                        button_unrounded.setMaximumWidth(20)
                        button_unrounded.setCheckable(True)
                        button_unrounded.setChecked(phoneme in self.vowel_inventory)
                        button_unrounded.clicked.connect(self._on_vowel_button_clicked)
                        button_layout.addWidget(button_unrounded)
                    # Add a left margin as we go down the rows
                    if j == 0:
                        button_layout.setContentsMargins(20*i, 0, 20*(I-i), 0)
                    elif j == 1:
                        button_layout.setContentsMargins(12*i, 0, 12*(I-i), 0)
                    if j >= J-1:
                        self.vowel_layout.addWidget(button_group, i+1, j+1, 1, 2)
                    else:
                        self.vowel_layout.addWidget(button_group, i+1, j+1)
                except KeyError:
                    pass
    
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
                if item != None:
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
                if item != None:
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
    logging.basicConfig(filename="phonology_selector.log", level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    app = QApplication([])
    window = PhonologySelector()
    window.show()
    app.exec()

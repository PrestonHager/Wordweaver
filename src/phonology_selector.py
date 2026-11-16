# phonology_selector.py

from PyQt6.QtWidgets import QApplication, QLineEdit, QMessageBox, QPushButton, QGridLayout, QHBoxLayout, QLabel, QMainWindow, QTextEdit, QVBoxLayout, QWidget
from PyQt6.QtGui import QFont, QPalette
from PyQt6.QtCore import Qt

import logging

from phonology import is_valid_phoneme
from phonology_const import PULMONIC_CONSONANTS, VOWELS
from wordweaver_project import Language

class PhonologySelector(QMainWindow):
    def __init__(self, language: Language=None):
        super().__init__()

        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)

        # Setup defaults for the class
        self.language = language
        # The chart is only a layout, every button edits this one list of symbols.
        # It's written back to the Language's Phoneme Inventory on Save & Close.
        self.inventory = language.inventory.symbols if language is not None else []

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
        self.selection = QTextEdit(', '.join(self.inventory), selection_group)
        self.selection.setMaximumHeight(50)
        self.selection.textChanged.connect(self.update_selection)
        selection_group_layout.addWidget(self.selection)
        self.content_layout.addWidget(selection_group, 1, 0, 1, 2)

        # Add a box for typing in sounds that aren't on the chart, like clicks or affricates.
        symbol_group = QWidget(self.content)
        symbol_group_layout = QHBoxLayout(symbol_group)
        symbol_group_layout.addWidget(QLabel("IPA symbol:", symbol_group))
        self.symbol_input = QLineEdit(symbol_group)
        self.symbol_input.setPlaceholderText("e.g. ǀ or t͡s")
        self.symbol_input.returnPressed.connect(self.add_symbol)
        symbol_group_layout.addWidget(self.symbol_input)
        add_symbol_button = QPushButton("Add", symbol_group)
        add_symbol_button.clicked.connect(self.add_symbol)
        symbol_group_layout.addWidget(add_symbol_button)
        remove_symbol_button = QPushButton("Remove", symbol_group)
        remove_symbol_button.clicked.connect(self.remove_symbol)
        symbol_group_layout.addWidget(remove_symbol_button)
        self.content_layout.addWidget(symbol_group, 2, 0, 1, 2)

        # Add the vowel selection table
        vowel_group = QWidget(self.content)
        self.vowel_layout = QGridLayout(vowel_group)
        self.content_layout.addWidget(vowel_group, 0, 1)

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
                        button_voiced.setChecked(phonemes["voiced"] in self.inventory)
                        button_voiced.clicked.connect(self._on_button_clicked)
                        button_layout.addWidget(button_voiced)
                    else:
                        button_layout.addStretch()
                    if "voiceless" in phonemes:
                        button_voiceless = QPushButton(phonemes["voiceless"])
                        button_voiceless.setProperty("phoneme", phonemes["voiceless"])
                        button_voiceless.setMinimumHeight(25)
                        button_voiceless.setMaximumWidth(20)
                        button_voiceless.setCheckable(True)
                        button_voiceless.setChecked(phonemes["voiceless"] in self.inventory)
                        button_voiceless.clicked.connect(self._on_button_clicked)
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
                        button_rounded.setChecked(phoneme in self.inventory)
                        button_rounded.clicked.connect(self._on_button_clicked)
                        button_layout.addWidget(button_rounded)
                    if "rounded" in phonemes:
                        phoneme = phonemes["rounded"]
                        button_unrounded = QPushButton(phoneme)
                        button_unrounded.setProperty("phoneme", phoneme)
                        button_unrounded.setMinimumHeight(25)
                        button_unrounded.setMaximumWidth(20)
                        button_unrounded.setCheckable(True)
                        button_unrounded.setChecked(phoneme in self.inventory)
                        button_unrounded.clicked.connect(self._on_button_clicked)
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
    
    def _on_button_clicked(self, checked):
        button = self.sender()
        phoneme = button.property("phoneme")
        self.logger.debug(f"Phoneme `{phoneme}` is now {'selected' if checked else 'deselected'}")
        if checked and phoneme not in self.inventory:
            self.inventory.append(phoneme)
        elif not checked and phoneme in self.inventory:
            self.inventory.remove(phoneme)
        # Update the text box
        self.selection.setText(', '.join(self.inventory))

    def add_symbol(self):
        symbol = self.symbol_input.text().strip()
        if not symbol:
            return
        # Check the symbol here, so nothing broken gets into the list.
        if not is_valid_phoneme(symbol):
            self.logger.warning(f"Not an IPA consonant or vowel: {symbol!r}")
            QMessageBox.warning(self, "Invalid Phoneme", f"{symbol} isn't an IPA consonant or vowel, so it wasn't added.")
            return
        if symbol not in self.inventory:
            self.inventory.append(symbol)
        self.symbol_input.clear()
        # Setting the text also checks the matching chart button, if there is one.
        self.selection.setText(', '.join(self.inventory))

    def remove_symbol(self):
        symbol = self.symbol_input.text().strip()
        if symbol not in self.inventory:
            QMessageBox.information(self, "Not in Inventory", f"{symbol} isn't in this Language's Phoneme Inventory.")
            return
        self.inventory.remove(symbol)
        self.symbol_input.clear()
        self.selection.setText(', '.join(self.inventory))

    def update_selection(self):
        self.logger.debug("Updating phoneme inventory from selection text box")
        self.inventory = [c.strip() for c in self.selection.toPlainText().split(",") if c.strip()]
        # Now check every button in both charts against the new list.
        for layout in (self.pulmonic_layout, self.vowel_layout):
            for i in range(1, layout.rowCount()):
                for j in range(1, layout.columnCount()):
                    item = layout.itemAtPosition(i, j)
                    if item is not None:
                        for k in range(item.widget().layout().count()):
                            button = item.widget().layout().itemAt(k).widget()
                            if button is not None:
                                button.setChecked(button.property("phoneme") in self.inventory)

    def save(self):
        # Write the selection into the Language, which keeps the IDs of Phonemes that stayed.
        if self.language is not None:
            try:
                self.language.inventory.set_symbols(self.inventory)
            except ValueError as e:
                self.logger.warning(str(e))
                QMessageBox.warning(self, "Invalid Phonemes", str(e))
                return
        self.close()

if __name__ == "__main__":
    logging.basicConfig(filename="phonology_selector.log", level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    app = QApplication([])
    window = PhonologySelector()
    window.show()
    app.exec()

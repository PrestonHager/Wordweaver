# phonology_selector.py

from PyQt6.QtWidgets import QApplication, QPushButton, QGridLayout, QHBoxLayout, QLabel, QMainWindow, QTextEdit, QVBoxLayout, QWidget
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from phonology_const import PULMONIC_CONSONANTS
from wordweaver_project import WordweaverProject

class PhonologySelector(QMainWindow):
    def __init__(self, project: WordweaverProject=None):
        super().__init__()

        # Setup defaults for the class
        self._project = project
        self.phonology_inventory = [p.sound_ascii for p in self._project.pulmonic_inventory] if self._project is not None else []

        # Construct GUI
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

        # Generate table of phonemes
        table_widget = QWidget(self)
        self.layout.addWidget(table_widget)
        self.grid_layout = QGridLayout(table_widget)

        self._add_phonology_const()

        # Add the selection preview
        selection_group = QWidget(self)
        selection_group_layout = QHBoxLayout(selection_group)

        selection_label = QLabel("Selected:", self)
        selection_group_layout.addWidget(selection_label)
        self.selection = QTextEdit(', '.join(self.phonology_inventory), selection_group)
        self.selection.setMaximumHeight(50)
        self.selection.textChanged.connect(self.update_selection)
        selection_group_layout.addWidget(self.selection)
        self.layout.addWidget(selection_group)

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

    def _add_phonology_const(self):
        manners = ["nasal", "plosive", "trill", "tap", "fricative", "lateral-fricative", "approximant", "lateral-approximant"]
        places = ["bi-labial", "labio-dental", "dental", "alveolar", "post-alveolar", "retroflex", "palatal", "velar", "uvular", "pharyngeal", "glottal"]
        # Add the labels
        for i in range(len(manners)):
            manner = manners[i]
            label = QLabel(manner, self)
            self.grid_layout.addWidget(label, i+1, 0)
        for j in range(len(places)):
            place = places[j]
            label = QLabel(place, self)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(label, 0, j+1)
        
        # Add the phonetic symbols
        for i in range(len(manners)):
            manner = manners[i]
            for j in range(len(places)):
                place = places[j]
                try:
                    phonemes = PULMONIC_CONSONANTS[manner][place]
                    button_group = QWidget()
                    button_layout = QHBoxLayout(button_group)
                    for phoneme in phonemes.keys():
                        # Create a button for each phoneme
                        button = QPushButton(phonemes[phoneme])
                        button.setProperty("phoneme", phoneme)
                        button.setMinimumHeight(25)
                        button.setMaximumWidth(20)
                        button.setCheckable(True)
                        button.setChecked(phoneme in self.phonology_inventory)
                        button.clicked.connect(self._on_phoneme_button_clicked)
                        button_layout.addWidget(button)
                    self.grid_layout.addWidget(button_group, i+1, j+1)
                except KeyError:
                    pass
    
    def _on_phoneme_button_clicked(self, checked):
        button = self.sender()
        phoneme = button.property("phoneme")
        if checked:
            self.phonology_inventory.append(phoneme)
        else:
            self.phonology_inventory.remove(phoneme)
        # Update the text box
        self.selection.setText(', '.join(self.phonology_inventory))
    
    def update_selection(self):
        self.phonology_inventory = self.selection.toPlainText().split(", ")
        for i in range(1, self.grid_layout.rowCount()):
            for j in range(1, self.grid_layout.columnCount()):
                item = self.grid_layout.itemAtPosition(i, j)
                if item != None:
                    for k in range(self.grid_layout.itemAtPosition(i, j).widget().layout().count()):
                        button = item.widget().layout().itemAt(k).widget()
                        phoneme = button.property("phoneme")
                        button.setChecked(phoneme in self.phonology_inventory)

    @property
    def project(self):
        # Update the project with the new phonology inventory
        if self._project is not None:
            self._project.pulmonic_inventory = self.phonology_inventory
        return self._project

    def save(self):
        self.close()

if __name__ == "__main__":
    app = QApplication([])
    window = PhonologySelector()
    window.show()
    app.exec()

# phonology_settings.py

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QCheckBox, QGridLayout, QHBoxLayout, QLineEdit, QWidget

from widgets import Button, Card, label
from wordweaver_project import Language

class FrequencyCard(Card):
    """Lets you give each Phoneme an optional Frequency. A blank box means it counts the same as the rest."""

    changed = pyqtSignal()  # pyright: ignore[reportCallIssue]  PyQt6 stub bug, see pyproject.

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.language: Language | None = None
        self.inputs: dict[str, QLineEdit] = {}
        self.content.addWidget(label("PHONEME FREQUENCY", "section"))
        self.content.addWidget(label("How common each Phoneme is, as a weight. Leave a box blank and that Phoneme counts as 1, so all blank means all equal.", "muted", self))
        self.grid_box = QWidget(self)
        self.grid = QGridLayout(self.grid_box)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.content.addWidget(self.grid_box)
        self.error = label("", "error", self)
        self.error.hide()
        self.content.addWidget(self.error)

    def set_language(self, language: Language | None):
        self.language = language
        self.refresh()

    def refresh(self):
        # First, clear out the old boxes.
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()
        self.inputs = {}
        if self.language is None:
            return
        # Then lay out a symbol and a box for each Phoneme, four to a row.
        columns = 4
        for i, symbol in enumerate(self.language.inventory.symbols):
            row, column = divmod(i, columns)
            symbol_label = label(symbol, parent=self.grid_box)
            symbol_label.setObjectName("FrequencySymbol")
            self.grid.addWidget(symbol_label, row, column * 2)
            box = QLineEdit(self.grid_box)
            box.setPlaceholderText("equal")
            box.setMaximumWidth(90)
            frequency = self.language.inventory.frequency(symbol)
            box.setText("" if frequency is None else f"{frequency:g}")
            box.editingFinished.connect(lambda s=symbol: self.save(s))
            self.grid.addWidget(box, row, column * 2 + 1)
            self.inputs[symbol] = box

    def save(self, symbol: str):
        if self.language is None or symbol not in self.language.inventory:
            return
        text = self.inputs[symbol].text().strip()
        try:
            self.language.inventory.set_frequency(symbol, float(text) if text else None)
        except ValueError:
            self._show_error(f"The Frequency for {symbol} has to be a positive number, or blank.")
            return
        self._show_error(None)
        self.changed.emit()

    def _show_error(self, message: str | None):
        self.error.setText(message or "")
        self.error.setVisible(message is not None)

class SuprasegmentalsCard(Card):
    """Lets you set whether a Language uses Stress and Length, and list its tones."""

    changed = pyqtSignal()  # pyright: ignore[reportCallIssue]  PyQt6 stub bug, see pyproject.

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.language: Language | None = None
        self.content.addWidget(label("SUPRASEGMENTALS", "section"))
        self.content.addWidget(label("Language-wide for now. Putting these on syllables comes with Phonotactics.", "muted", self))
        checks = QHBoxLayout()
        self.stress = QCheckBox("Uses Stress", self)
        self.stress.toggled.connect(self._on_stress)
        checks.addWidget(self.stress)
        self.length = QCheckBox("Uses Length", self)
        self.length.toggled.connect(self._on_length)
        checks.addWidget(self.length)
        checks.addStretch()
        self.content.addLayout(checks)
        tones = QHBoxLayout()
        tones.addWidget(label("Tones:", parent=self))
        self.tones = QLineEdit(self)
        self.tones.setPlaceholderText("None. Type names split by commas, like high, mid, low")
        self.tones.returnPressed.connect(self.save_tones)
        tones.addWidget(self.tones, 1)
        save = Button("Save Tones", "save", parent=self)
        save.clicked.connect(self.save_tones)
        tones.addWidget(save)
        self.content.addLayout(tones)
        self.error = label("", "error", self)
        self.error.hide()
        self.content.addWidget(self.error)

    def set_language(self, language: Language | None):
        self.language = language
        self.refresh()

    def refresh(self):
        settings = self.language.suprasegmentals if self.language is not None else None
        # Set the boxes without their signals, so showing a Language doesn't count as editing it.
        for box, value in ((self.stress, settings is not None and settings.stress), (self.length, settings is not None and settings.length)):
            box.blockSignals(True)
            box.setChecked(value)
            box.blockSignals(False)
        self.tones.setText(", ".join(settings.tones) if settings is not None else "")
        for widget in (self.stress, self.length, self.tones):
            widget.setEnabled(settings is not None)

    def _on_stress(self, on: bool):
        if self.language is not None:
            self.language.suprasegmentals.stress = on
            self.changed.emit()

    def _on_length(self, on: bool):
        if self.language is not None:
            self.language.suprasegmentals.length = on
            self.changed.emit()

    def save_tones(self):
        if self.language is None:
            return
        text = self.tones.text().strip()
        try:
            self.language.suprasegmentals.tones = [t for t in text.split(",")] if text else []
        except ValueError as e:
            self.error.setText(str(e))
            self.error.show()
            return
        self.error.hide()
        self.refresh()
        self.changed.emit()

__all__ = ["FrequencyCard", "SuprasegmentalsCard"]

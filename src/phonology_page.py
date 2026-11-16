# phonology_page.py

from PyQt6.QtCore import QPointF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QPolygonF
from PyQt6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLineEdit, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

import logging
import pyperclip

from classes_card import ClassesCard
from phonology import is_valid_phoneme
from phonology_const import PULMONIC_CONSONANTS, VOWELS
from theme import theme
from widgets import Button, Card, Chip, FlowLayout, PageHeader, label
from wordweaver_project import Language

# Chart rows and columns, in the order the IPA chart uses, with the names we show for them.
MANNERS = {
    "plosive": "Plosive",
    "nasal": "Nasal",
    "trill": "Trill",
    "tap": "Tap or flap",
    "fricative": "Fricative",
    "lateral-fricative": "Lateral\nfricative",
    "approximant": "Approximant",
    "lateral-approximant": "Lateral\napproximant",
}
PLACES = {
    "bi-labial": "Bilabial",
    "labio-dental": "Labio-\ndental",
    "dental": "Dental",
    "alveolar": "Alveolar",
    "post-alveolar": "Post-\nalveolar",
    "retroflex": "Retro-\nflex",
    "palatal": "Palatal",
    "velar": "Velar",
    "uvular": "Uvular",
    "pharyngeal": "Pharyn-\ngeal",
    "glottal": "Glottal",
}
HEIGHTS = ["close", "near-close", "close-mid", "mid", "open-mid", "near-open", "open"]
BACKNESS = ["front", "central", "back"]

PHONEME_SIZE = 32

def _plain(name: str) -> str:
    # Undo the line breaks in a chart label, so "Labio-\ndental" reads "labiodental".
    return name.replace("-\n", "").replace("\n", " ").lower()

def _describe() -> dict[str, str]:
    # Build a plain description of every chart symbol, like "voiceless bilabial plosive", for tooltips.
    descriptions = {}
    for manner, places in PULMONIC_CONSONANTS.items():
        for place, voicings in places.items():
            for voicing, symbol in voicings.items():
                descriptions[symbol] = f"{voicing} {_plain(PLACES[place])} {_plain(MANNERS[manner])}"
    for height, columns in VOWELS.items():
        for backness, roundings in columns.items():
            for rounding, symbol in roundings.items():
                descriptions[symbol] = f"{height} {backness} {rounding} vowel"
    return descriptions

DESCRIPTIONS = _describe()

class PhonemeButton(QPushButton):
    """A square toggle for one Phoneme on a chart."""

    def __init__(self, symbol: str, parent: QWidget | None = None):
        super().__init__(symbol, parent)
        self.setObjectName("Phoneme")
        self.symbol = symbol
        self.setCheckable(True)
        self.setFixedSize(PHONEME_SIZE, PHONEME_SIZE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(f"/{symbol}/ {DESCRIPTIONS.get(symbol, '')}")

class ConsonantChart(QWidget):
    """The pulmonic consonant chart, with voiceless sounds on the left of each cell and voiced on the right."""

    toggled = pyqtSignal(str, bool)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.buttons: dict[str, PhonemeButton] = {}
        grid = QGridLayout(self)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(0)
        # Only show the places that have at least one sound, so there are no empty columns.
        places = [p for p in PLACES if any(p in PULMONIC_CONSONANTS[m] for m in PULMONIC_CONSONANTS)]
        for j, place in enumerate(places):
            header = label(PLACES[place], "axis", self)
            header.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
            header.setContentsMargins(0, 0, 0, 6)
            grid.addWidget(header, 0, j + 1)
        for i, manner in enumerate(MANNERS):
            row = label(MANNERS[manner], "axis", self)
            row.setContentsMargins(0, 0, 10, 0)
            grid.addWidget(row, i + 1, 0)
            for j, place in enumerate(places):
                grid.addWidget(self._cell(PULMONIC_CONSONANTS.get(manner, {}).get(place, {})), i + 1, j + 1)

    def _cell(self, voicings: dict[str, str]) -> QFrame:
        cell = QFrame(self)
        cell.setObjectName("ChartCell")
        layout = QHBoxLayout(cell)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(2)
        # Keep an empty slot where a sound is missing, so every column lines up.
        for voicing in ("voiceless", "voiced"):
            if voicing in voicings:
                layout.addWidget(self._button(voicings[voicing]))
            else:
                spacer = QWidget(cell)
                spacer.setFixedSize(PHONEME_SIZE, PHONEME_SIZE)
                layout.addWidget(spacer)
        return cell

    def _button(self, symbol: str) -> PhonemeButton:
        button = PhonemeButton(symbol, self)
        button.clicked.connect(lambda checked, s=symbol: self.toggled.emit(s, checked))
        self.buttons[symbol] = button
        return button

class VowelChart(QWidget):
    """The vowel trapezoid, with unrounded vowels on the left of each point and rounded on the right."""

    toggled = pyqtSignal(str, bool)

    MARGIN_LEFT = 90
    MARGIN = 40

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.buttons: dict[str, PhonemeButton] = {}
        # Each entry is (height index, backness index, rounding, button).
        self._placed = []
        for i, height in enumerate(HEIGHTS):
            for j, backness in enumerate(BACKNESS):
                for rounding, symbol in VOWELS.get(height, {}).get(backness, {}).items():
                    button = PhonemeButton(symbol, self)
                    button.clicked.connect(lambda checked, s=symbol: self.toggled.emit(s, checked))
                    self.buttons[symbol] = button
                    self._placed.append((i, j, rounding, button))
        # Label the edges like the IPA chart does.
        self._axis = []
        for text in ("Front", "Central", "Back"):
            self._axis.append(label(text, "axis", self))
        for text in ("Close", "Close-mid", "Open-mid", "Open"):
            self._axis.append(label(text, "axis", self))
        self.setMinimumSize(520, 340)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        theme.changed.connect(self.update)

    def _corners(self) -> tuple[float, float, float, float, float]:
        # Return the top, bottom, top-left x, bottom-left x, and right x of the trapezoid.
        top, bottom = 34.0, self.height() - 26.0
        right = min(self.width() - self.MARGIN, self.MARGIN_LEFT + 480.0)
        left = float(self.MARGIN_LEFT)
        return top, bottom, left, left + (right - left) * 0.5, right

    def _point(self, i: float, j: float) -> QPointF:
        # Find where a height and backness sit inside the trapezoid.
        top, bottom, left, bottom_left, right = self._corners()
        t = i / (len(HEIGHTS) - 1)
        y = top + (bottom - top) * t
        front = left + (bottom_left - left) * t
        return QPointF(front + (right - front) * j / 2, y)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        half = PHONEME_SIZE / 2
        for i, j, rounding, button in self._placed:
            point = self._point(i, j)
            # Unrounded goes just left of the point and rounded just right, like the chart.
            x = point.x() - PHONEME_SIZE - 1 if rounding == "unrounded" else point.x() + 1
            button.move(int(x), int(point.y() - half))
        # Now place the edge labels.
        for j, axis in enumerate(self._axis[:3]):
            axis.adjustSize()
            point = self._point(0, j)
            axis.move(int(point.x() - axis.width() / 2), 0)
        for k, height in enumerate((0, 2, 4, 6)):
            axis = self._axis[3 + k]
            axis.adjustSize()
            point = self._point(height, 0)
            axis.move(int(point.x() - PHONEME_SIZE - axis.width() - 10), int(point.y() - axis.height() / 2))

    def paintEvent(self, event):
        # Draw the trapezoid and its guide lines behind the buttons.
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(theme.color("border")), 1.5))
        corners = [self._point(0, 0), self._point(0, 2), self._point(6, 2), self._point(6, 0)]
        painter.drawPolygon(QPolygonF(corners))
        for height in (2, 4):
            painter.drawLine(self._point(height, 0), self._point(height, 2))
        painter.drawLine(self._point(0, 1), self._point(6, 1))
        painter.end()

class PhonologyPage(QWidget):
    """Edit one Language's Phoneme Inventory, by clicking the charts or typing IPA symbols."""

    # Sent whenever the inventory changes, so other pages can update.
    changed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Page")
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self.language: Language | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)
        body = QWidget(scroll)
        scroll.setWidget(body)
        layout = QVBoxLayout(body)
        layout.setContentsMargins(32, 28, 32, 32)
        layout.setSpacing(16)

        # First, the header with the copy action.
        self.header = PageHeader("Phonology", "", body)
        copy = Button("Copy", "copy", tooltip="Copy the Phoneme Inventory", parent=body)
        copy.clicked.connect(self.copy)
        self.header.add_action(copy)
        layout.addWidget(self.header)

        # Then the inventory card, with chips for each Phoneme and a box to type more.
        inventory = Card(body)
        title_row = QHBoxLayout()
        title_row.addWidget(label("PHONEME INVENTORY", "section"))
        self.count = label("0", "badge")
        title_row.addWidget(self.count)
        title_row.addStretch()
        inventory.layout.addLayout(title_row)
        self.chips_box = QWidget(inventory)
        self.chips = FlowLayout(self.chips_box)
        inventory.layout.addWidget(self.chips_box)
        self.empty = label("No Phonemes yet. Click sounds on the charts below, or type one in.", "muted", inventory)
        inventory.layout.addWidget(self.empty)
        input_row = QHBoxLayout()
        self.symbol_input = QLineEdit(inventory)
        self.symbol_input.setObjectName("IpaInput")
        self.symbol_input.setPlaceholderText("Add a sound that's not on the charts, like ǀ or t͡s")
        self.symbol_input.textChanged.connect(self._check_input)
        self.symbol_input.returnPressed.connect(self.add_symbol)
        input_row.addWidget(self.symbol_input, 1)
        self.add_button = Button("Add", "plus", "primary", parent=inventory)
        self.add_button.clicked.connect(self.add_symbol)
        input_row.addWidget(self.add_button)
        inventory.layout.addLayout(input_row)
        self.error = label("", "error", inventory)
        self.error.hide()
        inventory.layout.addWidget(self.error)
        layout.addWidget(inventory)

        # Then the Phoneme Classes, which group the inventory.
        self.classes_card = ClassesCard(body)
        self.classes_card.changed.connect(self._on_classes_changed)
        layout.addWidget(self.classes_card)

        # Now the two charts, each in its own card.
        consonants = Card(body)
        consonants.layout.addWidget(label("PULMONIC CONSONANTS", "section"))
        consonants.layout.addWidget(label("Voiceless sounds are on the left of each cell, voiced on the right.", "muted"))
        # The chart is wide, so it scrolls sideways by itself instead of stretching the whole page.
        chart_scroll = QScrollArea(consonants)
        chart_scroll.setFrameShape(QFrame.Shape.NoFrame)
        chart_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.consonant_chart = ConsonantChart(chart_scroll)
        self.consonant_chart.toggled.connect(self.toggle)
        chart_scroll.setWidget(self.consonant_chart)
        chart_scroll.setMinimumHeight(self.consonant_chart.sizeHint().height() + 14)
        consonants.layout.addWidget(chart_scroll)
        vowels = Card(body)
        vowels.layout.addWidget(label("VOWELS", "section"))
        vowels.layout.addWidget(label("Unrounded vowels are on the left of each point, rounded on the right.", "muted"))
        self.vowel_chart = VowelChart(vowels)
        self.vowel_chart.toggled.connect(self.toggle)
        vowels.layout.addWidget(self.vowel_chart)
        layout.addWidget(consonants)
        layout.addWidget(vowels)
        layout.addStretch()

        self.buttons = {**self.consonant_chart.buttons, **self.vowel_chart.buttons}

    def set_language(self, language: Language | None):
        self.language = language
        self.symbol_input.clear()
        self.classes_card.set_language(language)
        self.refresh()

    def refresh(self):
        # Match the page to the Language's inventory: subtitle, chips, then chart buttons.
        symbols = self.language.inventory.symbols if self.language is not None else []
        name = self.language.name if self.language is not None else ""
        self.header.subtitle.setText(f"The sounds {name} uses. Click a sound on a chart to add or remove it.")
        self.count.setText(str(len(symbols)))
        self.chips.clear()
        for symbol in symbols:
            classes = ", ".join(c.name for c in self.language.classes_of(symbol))
            tooltip = DESCRIPTIONS.get(symbol, "Off-chart Phoneme") + (f"\nClasses: {classes}" if classes else "")
            chip = Chip(symbol, tooltip, self.chips_box)
            chip.removed.connect(lambda s: self.toggle(s, False))
            self.chips.addWidget(chip)
        self.chips_box.setVisible(bool(symbols))
        self.empty.setVisible(not symbols)
        for symbol, button in self.buttons.items():
            button.setChecked(symbol in symbols)
        self.classes_card.refresh()

    def _on_classes_changed(self):
        # Class edits change the chip tooltips, so redraw those too.
        self.refresh()
        self.changed.emit()

    def toggle(self, symbol: str, on: bool):
        if self.language is None:
            return
        inventory = self.language.inventory
        if on and symbol not in inventory:
            inventory.add(symbol)
        elif not on and symbol in inventory:
            inventory.remove(symbol)
        self.logger.debug(f"Phoneme `{symbol}` is now {'selected' if on else 'deselected'}")
        self.refresh()
        self.changed.emit()

    def _check_input(self, text: str):
        # Warn as they type, instead of waiting for them to press Add.
        symbol = text.strip()
        if symbol and not is_valid_phoneme(symbol):
            self._show_error(f"{symbol} isn't an IPA consonant or vowel.")
        elif symbol and self.language is not None and symbol in self.language.inventory:
            self._show_error(f"{symbol} is already in the inventory.")
        else:
            self._show_error(None)

    def _show_error(self, message: str | None):
        self.error.setText(message or "")
        self.error.setVisible(message is not None)
        self.add_button.setEnabled(message is None)
        self.symbol_input.setProperty("invalid", message is not None)
        # Qt only re-reads a property selector when the style is reapplied.
        self.symbol_input.style().unpolish(self.symbol_input)
        self.symbol_input.style().polish(self.symbol_input)

    def add_symbol(self):
        symbol = self.symbol_input.text().strip()
        if not symbol or not is_valid_phoneme(symbol) or self.language is None:
            return
        self.symbol_input.clear()
        self.toggle(symbol, True)

    def copy(self):
        if self.language is not None:
            pyperclip.copy(", ".join(self.language.inventory.symbols))

__all__ = ["PhonologyPage", "ConsonantChart", "VowelChart", "DESCRIPTIONS"]

# allophones_card.py

from typing import Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QWidget

from allophones import WORD_BOUNDARY, AllophoneRule, ContextSide
from widgets import Button, Card, label
from wordweaver_project import Language

class _OptionPicker(QComboBox):
    """A combo box that keeps the Python value behind each of its items."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.options: list[tuple[str, Any]] = []

class AllophonesCard(Card):
    """Lists a Language's Allophone Rules and lets you add, edit, and remove them."""

    # Sent whenever a rule changes, so other pages can update.
    changed = pyqtSignal()  # pyright: ignore[reportCallIssue]  PyQt6 stub bug, see pyproject.

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.language: Language | None = None
        self.selected: AllophoneRule | None = None

        # First, the title and a short how-to.
        title_row = QHBoxLayout()
        title_row.addWidget(label("ALLOPHONE RULES", "section"))
        self.count = label("0", "badge")
        title_row.addWidget(self.count)
        title_row.addStretch()
        self.content.addLayout(title_row)
        self.content.addWidget(label("How a Phoneme is pronounced in a context, like /t/ → [ɾ] / Vowel _ Vowel. # is the edge of a word.", "muted", self))

        # Then the list of rules.
        self.list = QListWidget(self)
        self.list.setMinimumHeight(120)
        self.list.currentItemChanged.connect(self._on_picked)
        self.content.addWidget(self.list)

        # Now the form, which reads /phoneme/ → [allophone] / before _ after.
        form = QHBoxLayout()
        self.phoneme_picker = _OptionPicker(self)
        self.phoneme_picker.setToolTip("The Phoneme")
        form.addWidget(self.phoneme_picker)
        form.addWidget(label("→", parent=self))
        self.allophone_input = QLineEdit(self)
        self.allophone_input.setObjectName("IpaInput")
        self.allophone_input.setPlaceholderText("Allophone, like ɾ")
        self.allophone_input.returnPressed.connect(self.save_rule)
        self.allophone_input.setMaximumWidth(180)
        form.addWidget(self.allophone_input)
        form.addWidget(label("/", parent=self))
        self.before_picker = _OptionPicker(self)
        self.before_picker.setToolTip("What comes before")
        form.addWidget(self.before_picker)
        form.addWidget(label("_", parent=self))
        self.after_picker = _OptionPicker(self)
        self.after_picker.setToolTip("What comes after")
        form.addWidget(self.after_picker)
        form.addStretch()
        self.content.addLayout(form)

        # Finally, the buttons and a place for errors.
        buttons = QHBoxLayout()
        self.add_button = Button("Add Rule", "plus", "primary", parent=self)
        self.add_button.clicked.connect(self.add_rule)
        buttons.addWidget(self.add_button)
        self.save_button = Button("Save Changes", "save", parent=self)
        self.save_button.clicked.connect(self.save_rule)
        buttons.addWidget(self.save_button)
        self.remove_button = Button("Remove", "trash-2", "danger", parent=self)
        self.remove_button.clicked.connect(self.remove_rule)
        buttons.addWidget(self.remove_button)
        buttons.addStretch()
        self.content.addLayout(buttons)
        self.error = label("", "error", self)
        self.error.hide()
        self.content.addWidget(self.error)

    def set_language(self, language: Language | None):
        self.language = language
        self.selected = None
        self.allophone_input.clear()
        self.refresh()

    def refresh(self):
        rules = self.language.allophone_rules if self.language is not None else []
        if self.selected not in rules:
            self.selected = None
        # First, refill the list of rules.
        self.list.blockSignals(True)
        self.list.clear()
        for rule in rules:
            item = QListWidgetItem(str(rule), self.list)
            item.setData(Qt.ItemDataRole.UserRole, rule.id)
            if rule is self.selected:
                self.list.setCurrentItem(item)
        self.list.blockSignals(False)
        self.count.setText(str(len(rules)))
        # Then refill the pickers, keeping what they had picked if it's still there.
        symbols = self.language.inventory.symbols if self.language is not None else []
        self._fill(self.phoneme_picker, [(f"/{s}/", s) for s in symbols])
        sides = [("anything", None), ("# word edge", WORD_BOUNDARY)]
        if self.language is not None:
            sides += [(c.name, c) for c in self.language.classes if c.phonemes or not c.is_default]
            sides += [(f"/{p.symbol}/", p) for p in self.language.inventory]
        self._fill(self.before_picker, sides)
        self._fill(self.after_picker, sides)
        self._show_selected()

    def _fill(self, picker: _OptionPicker, options: list[tuple[str, Any]]):
        # QComboBox can't compare Python objects, so keep them in a list and store their index.
        current = picker.currentData()
        old = picker.options
        current_value = old[current][1] if current is not None and current < len(old) else None
        picker.blockSignals(True)
        picker.clear()
        picker.options = options
        for i, option in enumerate(options):
            picker.addItem(option[0], i)
        self._pick(picker, current_value)
        picker.blockSignals(False)

    def _pick(self, picker: _OptionPicker, value):
        for i, option_data in enumerate(picker.options):
            option = option_data[1]
            if option is value or (isinstance(value, str) and option == value):
                picker.setCurrentIndex(i)
                return
        picker.setCurrentIndex(0 if picker.count() else -1)

    def _value(self, picker: _OptionPicker) -> Any:
        index = picker.currentData()
        return picker.options[index][1] if index is not None else None

    def _on_picked(self, item: QListWidgetItem | None):
        if item is None or self.language is None:
            self.selected = None
        else:
            id = item.data(Qt.ItemDataRole.UserRole)
            self.selected = next((r for r in self.language.allophone_rules if r.id == id), None)
        self._show_error(None)
        self._show_selected()

    def _show_selected(self):
        # Load the picked rule into the form, so it can be changed and saved.
        rule = self.selected
        self.save_button.setEnabled(rule is not None)
        self.remove_button.setEnabled(rule is not None)
        self.add_button.setEnabled(self.language is not None and len(self.language.inventory) > 0)
        if rule is None:
            return
        self._pick(self.phoneme_picker, rule.phoneme.symbol)
        self.allophone_input.setText(rule.allophone)
        self._pick(self.before_picker, rule.before)
        self._pick(self.after_picker, rule.after)

    def _form(self) -> tuple[str, str, ContextSide, ContextSide]:
        return (self._value(self.phoneme_picker), self.allophone_input.text().strip(),
                self._value(self.before_picker), self._value(self.after_picker))

    def add_rule(self):
        if self.language is None:
            return
        phoneme, allophone, before, after = self._form()
        try:
            self.selected = self.language.add_allophone_rule(phoneme, allophone, before, after)
        except ValueError as e:
            self._show_error(str(e))
            return
        self._done()

    def save_rule(self):
        if self.selected is None:
            self.add_rule()
            return
        try:
            self.selected.edit(*self._form())
        except ValueError as e:
            self._show_error(str(e))
            return
        self._done()

    def remove_rule(self):
        if self.selected is None or self.language is None:
            return
        self.language.remove_allophone_rule(self.selected)
        self.selected = None
        self.allophone_input.clear()
        self._done()

    def _done(self):
        self._show_error(None)
        self.refresh()
        self.changed.emit()

    def _show_error(self, message: str | None):
        self.error.setText(message or "")
        self.error.setVisible(message is not None)

__all__ = ["AllophonesCard"]

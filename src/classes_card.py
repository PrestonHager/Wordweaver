# classes_card.py

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QCheckBox, QHBoxLayout, QInputDialog, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget

from phoneme_classes import PhonemeClass
from widgets import Button, Card, FlowLayout, label
from wordweaver_project import Language

class ClassesCard(Card):
    """Shows a Language's Phoneme Classes and lets you make, rename, delete, and fill them."""

    # Sent whenever a Class changes, so other pages can update.
    changed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.language: Language | None = None
        self.selected: PhonemeClass | None = None

        # First, the title row with the new Class button.
        title_row = QHBoxLayout()
        title_row.addWidget(label("PHONEME CLASSES", "section"))
        self.count = label("0", "badge")
        title_row.addWidget(self.count)
        title_row.addStretch()
        self.show_empty = QCheckBox("Show empty Classes", self)
        self.show_empty.toggled.connect(self.refresh)
        title_row.addWidget(self.show_empty)
        new_button = Button("New Class", "plus", parent=self)
        new_button.clicked.connect(self.new_class)
        title_row.addWidget(new_button)
        self.layout.addLayout(title_row)
        self.layout.addWidget(label("Default Classes fill in from IPA features. Once you change which Phonemes are in one, it stops filling in by itself.", "muted", self))

        # Then the list of Classes on the left and the picked Class on the right.
        body = QHBoxLayout()
        self.list = QListWidget(self)
        self.list.setMinimumWidth(200)
        self.list.setMinimumHeight(240)
        self.list.currentItemChanged.connect(self._on_picked)
        body.addWidget(self.list)
        editor = QWidget(self)
        editor_layout = QVBoxLayout(editor)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        name_row = QHBoxLayout()
        self.name_input = QLineEdit(editor)
        self.name_input.setPlaceholderText("Class name")
        self.name_input.returnPressed.connect(self.rename)
        name_row.addWidget(self.name_input, 1)
        # The short label is what Syllable Structures use, like C in (C)V(C).
        self.label_input = QLineEdit(editor)
        self.label_input.setPlaceholderText("Label")
        self.label_input.setToolTip("A short label for Syllable Structures, like C, V, or N")
        self.label_input.setMaximumWidth(80)
        self.label_input.returnPressed.connect(self.rename)
        name_row.addWidget(self.label_input)
        self.rename_button = Button("Save", "pencil", tooltip="Save the name and label", parent=editor)
        self.rename_button.clicked.connect(self.rename)
        name_row.addWidget(self.rename_button)
        self.delete_button = Button(icon="trash-2", variant="danger", tooltip="Delete this Class", parent=editor)
        self.delete_button.clicked.connect(self.delete)
        name_row.addWidget(self.delete_button)
        editor_layout.addLayout(name_row)
        self.status = label("", "muted", editor)
        self.status.setWordWrap(True)
        editor_layout.addWidget(self.status)
        editor_layout.addWidget(label("Click a Phoneme to put it in or take it out of this Class.", "muted", editor))
        self.members_box = QWidget(editor)
        self.members = FlowLayout(self.members_box)
        editor_layout.addWidget(self.members_box)
        self.error = label("", "error", editor)
        self.error.hide()
        editor_layout.addWidget(self.error)
        editor_layout.addStretch()
        body.addWidget(editor, 1)
        self.layout.addLayout(body)

    def set_language(self, language: Language | None):
        self.language = language
        self.selected = None
        self.refresh()

    def refresh(self):
        # First, refill the list, keeping the picked Class picked if it's still there.
        classes = self.language.classes if self.language is not None else []
        if self.selected not in classes:
            self.selected = None
        self.list.blockSignals(True)
        self.list.clear()
        shown = 0
        for phoneme_class in classes:
            size = len(phoneme_class.phonemes)
            # Hide empty default Classes unless asked, since most Languages leave lots of them empty.
            if phoneme_class.is_default and size == 0 and not self.show_empty.isChecked() and phoneme_class is not self.selected:
                continue
            text = f"{phoneme_class.name}  ({size})"
            if phoneme_class.label:
                text = f"{phoneme_class.label}  ·  " + text
            if not phoneme_class.is_default:
                text += "  · yours"
            elif phoneme_class.is_hand_edited:
                text += "  · edited"
            item = QListWidgetItem(text, self.list)
            item.setData(Qt.ItemDataRole.UserRole, phoneme_class.id)
            if phoneme_class is self.selected:
                self.list.setCurrentItem(item)
            shown += 1
        self.list.blockSignals(False)
        self.count.setText(str(shown))
        # Then show the picked Class.
        self._show_selected()

    def _on_picked(self, item: QListWidgetItem | None, _previous=None):
        if item is None or self.language is None:
            self.selected = None
        else:
            id = item.data(Qt.ItemDataRole.UserRole)
            self.selected = next((c for c in self.language.classes if c.id == id), None)
        self._show_error(None)
        self._show_selected()

    def _show_selected(self):
        selected = self.selected
        for widget in (self.name_input, self.label_input, self.rename_button, self.members_box):
            widget.setEnabled(selected is not None)
        self.delete_button.setEnabled(selected is not None and not selected.is_default)
        self.name_input.setText(selected.name if selected is not None else "")
        self.label_input.setText(selected.label if selected is not None else "")
        if selected is None:
            self.status.setText("Pick a Class to see its Phonemes.")
        elif not selected.is_default:
            self.status.setText("One of your own Classes.")
        elif selected.is_hand_edited:
            self.status.setText("A default Class you've edited, so new Phonemes aren't added to it by themselves.")
        else:
            self.status.setText("A default Class, filled in from IPA features.")
        # Now a toggle for every Phoneme in the inventory, checked if it's in the Class.
        self.members.clear()
        if selected is None or self.language is None:
            return
        for symbol in self.language.inventory.symbols:
            button = QPushButton(symbol, self.members_box)
            button.setObjectName("Phoneme")
            button.setCheckable(True)
            button.setChecked(symbol in selected)
            button.setFixedSize(36, 36)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.toggled.connect(lambda on, s=symbol: self.toggle(s, on))
            self.members.addWidget(button)

    def toggle(self, symbol: str, on: bool):
        if self.selected is None:
            return
        if on:
            self.selected.add(symbol)
        else:
            self.selected.remove(symbol)
        self.refresh()
        self.changed.emit()

    def new_class(self):
        if self.language is None:
            return
        name, ok = QInputDialog.getText(self, "New Phoneme Class", "Enter a name for the new Class:")
        if not ok:
            return
        try:
            self.selected = self.language.add_class(name.strip())
        except ValueError as e:
            self._show_error(str(e))
            return
        self._show_error(None)
        self.refresh()
        self.changed.emit()

    def rename(self):
        # Save both the name and the label, checking both first so a bad one changes neither.
        if self.selected is None:
            return
        name, new_label = self.name_input.text().strip(), self.label_input.text().strip()
        old_name, old_label = self.selected.name, self.selected.label
        try:
            self.selected.name = name
            self.selected.label = new_label
        except ValueError as e:
            self.selected.name = old_name
            self.selected.label = old_label
            self._show_error(str(e))
            return
        self._show_error(None)
        self.refresh()
        self.changed.emit()

    def delete(self):
        if self.selected is None or self.selected.is_default or self.language is None:
            return
        self.language.remove_class(self.selected)
        self.selected = None
        self.refresh()
        self.changed.emit()

    def _show_error(self, message: str | None):
        self.error.setText(message or "")
        self.error.setVisible(message is not None)

__all__ = ["ClassesCard"]

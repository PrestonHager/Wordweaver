# entry_editor.py

from dataclasses import dataclass, field

from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
                             QMessageBox, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget)

from lexicon import Definition, Entry, Form
from wordweaver_project import Language

@dataclass
class _DefinitionDraft:
    # A Definition as it's being edited, so nothing changes in the Lexicon until you press OK.
    definition: Definition | None = None
    glosses: list[str] = field(default_factory=list)
    terms: list[str] = field(default_factory=list)
    description: str = ""

    def label(self, number: int) -> str:
        glosses = "; ".join(g.strip() for g in self.glosses if g.strip())
        return f"{number}. {glosses or '(no Glosses yet)'}"

class EntryEditor(QDialog):
    """A dialog for adding a new Entry to a Language's Lexicon, or editing one that's already there."""

    def __init__(self, language: Language, entry: Entry | None=None, parent: QWidget | None=None):
        super().__init__(parent)
        self.language = language
        self.entry = entry
        self.setWindowTitle("Edit Entry" if entry is not None else "Add Entry")
        if entry is None:
            self._drafts = [_DefinitionDraft()]
        else:
            self._drafts = [_DefinitionDraft(d, list(d.glosses), list(d.terms), d.description) for d in entry.definitions]
        self._current = -1

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.form_input = QLineEdit(self)
        self.form_input.setPlaceholderText("IPA, like kata")
        form_layout.addRow("Form:", self.form_input)
        layout.addLayout(form_layout)

        # First, the list of Definitions with buttons to add, remove, and reorder them.
        self.definition_list = QListWidget(self)
        self.definition_list.currentRowChanged.connect(self._on_definition_picked)
        layout.addWidget(self.definition_list)
        definition_buttons = QHBoxLayout()
        for text, slot in (("Add Definition", self._add_definition), ("Remove Definition", self._remove_definition),
                           ("Move Up", lambda: self._move_definition(-1)), ("Move Down", lambda: self._move_definition(1))):
            button = QPushButton(text, self)
            button.clicked.connect(slot)
            definition_buttons.addWidget(button)
        layout.addLayout(definition_buttons)

        # Then the fields for the picked Definition.
        definition_layout = QFormLayout()
        self.glosses_input = QPlainTextEdit(self)
        self.glosses_input.setPlaceholderText("One Gloss per line")
        self.glosses_input.textChanged.connect(self._on_glosses_changed)
        definition_layout.addRow("Glosses:", self.glosses_input)
        self.terms_input = QPlainTextEdit(self)
        self.terms_input.setPlaceholderText("Optional, one technical term per line")
        definition_layout.addRow("Technical terms:", self.terms_input)
        self.description_input = QPlainTextEdit(self)
        self.description_input.setPlaceholderText("Optional, describe the meaning in your own words")
        definition_layout.addRow("Description:", self.description_input)
        layout.addLayout(definition_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if entry is not None:
            self.form_input.setText(str(entry.form))
        self._refresh_list(0)

    def _refresh_list(self, row: int):
        # Rebuild the list. Callers save the fields first, since the drafts may have moved since.
        self._current = -1
        self.definition_list.blockSignals(True)
        self.definition_list.clear()
        for number, draft in enumerate(self._drafts, start=1):
            self.definition_list.addItem(draft.label(number))
        # Adding items can pick a row without a signal, so load the fields by hand.
        self.definition_list.setCurrentRow(row)
        self.definition_list.blockSignals(False)
        self._on_definition_picked(row)

    def _store_fields(self):
        # Copy what's in the fields back into the draft they were showing.
        if not 0 <= self._current < len(self._drafts):
            return
        draft = self._drafts[self._current]
        draft.glosses = self.glosses_input.toPlainText().splitlines()
        draft.terms = self.terms_input.toPlainText().splitlines()
        draft.description = self.description_input.toPlainText()

    def _on_definition_picked(self, row: int):
        self._store_fields()
        self._current = row
        if not 0 <= row < len(self._drafts):
            return
        draft = self._drafts[row]
        self.glosses_input.blockSignals(True)
        self.glosses_input.setPlainText("\n".join(draft.glosses))
        self.glosses_input.blockSignals(False)
        self.terms_input.setPlainText("\n".join(draft.terms))
        self.description_input.setPlainText(draft.description)

    def _on_glosses_changed(self):
        # Keep the list label in step with the Glosses as you type.
        if 0 <= self._current < len(self._drafts):
            self._store_fields()
            self.definition_list.item(self._current).setText(self._drafts[self._current].label(self._current + 1))

    def _add_definition(self):
        self._store_fields()
        self._drafts.append(_DefinitionDraft())
        self._refresh_list(len(self._drafts) - 1)
        self.glosses_input.setFocus()

    def _remove_definition(self):
        # Every Entry needs a Definition, so the last one stays.
        if len(self._drafts) == 1:
            QMessageBox.information(self, "Can't Remove Definition", "An Entry needs at least one Definition.")
            return
        row = self._current
        self._current = -1
        del self._drafts[row]
        self._refresh_list(min(row, len(self._drafts) - 1))

    def _move_definition(self, step: int):
        row = self._current
        if not 0 <= row + step < len(self._drafts):
            return
        self._store_fields()
        self._drafts[row], self._drafts[row + step] = self._drafts[row + step], self._drafts[row]
        self._refresh_list(row + step)

    def accept(self):
        self._store_fields()
        # First, check every Definition has a Gloss, so a bad one doesn't leave the Entry half saved.
        for number, draft in enumerate(self._drafts, start=1):
            if not any(g.strip() for g in draft.glosses):
                QMessageBox.warning(self, "Can't Save Entry", f"Definition {number} needs at least one Gloss.")
                self.definition_list.setCurrentRow(number - 1)
                return
        # Now split the Form using the Language's Phonemes, so multi-letter ones stay whole.
        form = Form.parse(self.form_input.text(), self.language.inventory.symbols)
        # Next, check for Homophones, which you can still save anyway.
        if not self._check_homophones(form):
            return
        lexicon = self.language.lexicon
        # Then write the drafts into the Lexicon, adding new Definitions before removing old ones so one is always left.
        if self.entry is None:
            first = self._drafts[0]
            self.entry = lexicon.add(form, first.glosses, first.terms, first.description)
            first.definition = self.entry.definitions[0]
        else:
            lexicon.edit(self.entry, form=form)
        for draft in self._drafts:
            if draft.definition is None:
                draft.definition = lexicon.add_definition(self.entry, draft.glosses, draft.terms, draft.description)
            else:
                lexicon.edit_definition(self.entry, draft.definition, draft.glosses, draft.terms, draft.description)
        kept = [draft.definition for draft in self._drafts]
        for definition in self.entry.definitions:
            if all(definition is not k for k in kept):
                lexicon.remove_definition(self.entry, definition)
        # Finally, put the Definitions in the order they're listed.
        for index, definition in enumerate(kept):
            lexicon.move_definition(self.entry, definition, index)
        super().accept()

    def _check_homophones(self, form: Form) -> bool:
        # Only warn when the Form is new, so editing a known Homophone's Glosses doesn't nag every time.
        if self.entry is not None and self.entry.form == form:
            return True
        matches = self.language.lexicon.homophones_of(form, exclude=self.entry)
        if not matches:
            return True
        warning = HomophoneWarning(form, matches, self)
        if warning.exec() == QDialog.DialogCode.Accepted:
            return True
        # Open the picked match in its own editor, then come back here so you can decide again.
        if warning.opened is not None:
            EntryEditor(self.language, warning.opened, parent=self).exec()
        return False

class HomophoneWarning(QDialog):
    """Lists the Entries that already have a Form, so you can open one or save a Homophone anyway."""

    def __init__(self, form: Form, matches: list[Entry], parent: QWidget | None=None):
        super().__init__(parent)
        self.matches = matches
        self.opened: Entry | None = None
        self.setWindowTitle("Homophone")

        layout = QVBoxLayout(self)
        count = "An Entry already has" if len(matches) == 1 else f"{len(matches)} Entries already have"
        layout.addWidget(QLabel(f"{count} the Form /{form}/.\nOpen one to add a Definition to it, or save a separate Homophone anyway.", self))
        self.match_list = QListWidget(self)
        for entry in matches:
            self.match_list.addItem(f"/{entry.form}/  {'; '.join(entry.glosses)}")
        self.match_list.setCurrentRow(0)
        self.match_list.itemDoubleClicked.connect(lambda _item: self.open_match())
        layout.addWidget(self.match_list)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel, self)
        buttons.addButton("Open Entry", QDialogButtonBox.ButtonRole.ActionRole).clicked.connect(self.open_match)
        buttons.addButton("Save Anyway", QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def open_match(self):
        self.opened = self.matches[max(self.match_list.currentRow(), 0)]
        self.reject()

__all__ = ["EntryEditor", "HomophoneWarning"]

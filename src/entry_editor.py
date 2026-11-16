# entry_editor.py

from dataclasses import dataclass, field

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
                             QMessageBox, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget)

from concepticon import concepticon_lookup
from lexicon import ConceptReference, Definition, Entry, Form, FormCheck, check_form
from sense_picker import SensePicker
from senses import Sense, SenseLookup, lookup_for
from tag_widgets import TagPicker
from widgets import label
from wordweaver_project import DEFAULT_GLOSS_LANGUAGE, Language

@dataclass
class _DefinitionDraft:
    # A Definition as it's being edited, so nothing changes in the Lexicon until you press OK.
    definition: Definition | None = None
    glosses: list[str] = field(default_factory=list)
    terms: list[str] = field(default_factory=list)
    description: str = ""
    concept_reference: ConceptReference | None = None
    # The linked sense's details, if it was picked in this editor. Saved references only keep their ID.
    sense: Sense | None = None

    def label(self, number: int) -> str:
        glosses = "; ".join(g.strip() for g in self.glosses if g.strip())
        return f"{number}. {glosses or '(no Glosses yet)'}"

    def reference_text(self) -> str:
        if self.concept_reference is None:
            return "None linked"
        if self.sense is not None:
            return f"{self.sense.label()}\n{self.concept_reference}"
        return str(self.concept_reference)

class FormWarnings(QWidget):
    """The Form check's warnings, shown under the Form field, with a button to add each unknown Phoneme to the Inventory."""

    phoneme_added = pyqtSignal(str)  # pyright: ignore[reportCallIssue]  PyQt6 stub bug, see pyproject.

    def __init__(self, language: Language, parent: QWidget | None=None):
        super().__init__(parent)  # pyright: ignore[reportArgumentType]  PyQt6 stub bug, see pyproject.
        self.language = language
        self.check = FormCheck()
        self.add_buttons: dict[str, QPushButton] = {}
        self._text = ""
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.hide()

    def update_form(self, text: str):
        """Check the Form text again and redraw the warnings."""
        self._text = text
        self.check = check_form(text, self.language.inventory.symbols)
        # First, clear out the old warnings.
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.setParent(None)  # pyright: ignore[reportArgumentType]  PyQt6 stub bug, see pyproject.
                widget.deleteLater()
        self.add_buttons = {}
        # Then give each unknown Phoneme a row with its own button.
        for symbol in self.check.unknown:
            row = QWidget(self)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.addWidget(label(f"/{symbol}/ isn't in the Phoneme Inventory.", "error", row), 1)
            button = QPushButton("Add to Inventory", row)
            button.clicked.connect(lambda _checked=False, s=symbol: self.add_phoneme(s))
            row_layout.addWidget(button)
            self.add_buttons[symbol] = button
            self._layout.addWidget(row)
        # Invalid IPA can't go in the Inventory, so it just gets a note.
        for text in self.check.invalid:
            self._layout.addWidget(label(f"{text} isn't an IPA consonant or vowel.", "error", self))
        self.setVisible(not self.check.ok)

    def add_phoneme(self, symbol: str):
        # Add it the same way the Phonology page does, so it's validated and gets an ID like any other Phoneme.
        self.language.inventory.add(symbol)
        self.phoneme_added.emit(symbol)
        self.update_form(self._text)

class EntryEditor(QDialog):
    """A dialog for adding a new Entry to a Language's Lexicon, or editing one that's already there.

    The Form is checked against the Phoneme Inventory as you type. It only warns, so the Entry can always be saved.
    """

    def __init__(self, language: Language, entry: Entry | None=None, parent: QWidget | None=None,
                 gloss_language: str=DEFAULT_GLOSS_LANGUAGE, senses: SenseLookup | None=None, concepts: SenseLookup | None=None):
        """
        :param gloss_language: str: The Project's Gloss Language, which picks the dictionary to search.
        :param senses: SenseLookup | None: The dictionary to search, instead of the one for the Gloss Language.
        :param concepts: SenseLookup | None: The Concepticon lookup to search, instead of the app's own.
        """
        super().__init__(parent)
        self.language = language
        self.entry = entry
        self.gloss_language = gloss_language
        self._senses = senses
        self._concepts = concepts
        self.setWindowTitle("Edit Entry" if entry is not None else "Add Entry")
        if entry is None:
            self._drafts = [_DefinitionDraft()]
        else:
            self._drafts = [_DefinitionDraft(d, list(d.glosses), list(d.terms), d.description, d.concept_reference) for d in entry.definitions]
        self._current = -1
        # Phonemes added to the Inventory from the Form warnings, so the page can refresh anything showing it.
        self.added_phonemes: list[str] = []

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.form_input = QLineEdit(self)
        self.form_input.setPlaceholderText("IPA, like kata")
        form_layout.addRow("Form:", self.form_input)
        self.form_warnings = FormWarnings(language, self)
        self.form_warnings.phoneme_added.connect(self.added_phonemes.append)
        self.form_input.textChanged.connect(self.form_warnings.update_form)
        form_layout.addRow("", self.form_warnings)
        # Tags go with the whole Entry, not one Definition, so they sit up here by the Form.
        # They're kept in their own widget, since they belong to the Project and not the Entry.
        self.tag_picker = None
        if language.lexicon.tags is not None:
            self.tag_picker = TagPicker(language.lexicon.tags, entry, self)
            form_layout.addRow("Tags:", self.tag_picker)
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
        # The Concept Reference is optional, so it's just a label with buttons to link or unlink a sense.
        reference_row = QHBoxLayout()
        self.reference_label = QLabel(self)
        self.reference_label.setWordWrap(True)
        reference_row.addWidget(self.reference_label, 1)
        self.link_button = QPushButton("Link Sense…", self)
        self.link_button.clicked.connect(self.link_sense)
        reference_row.addWidget(self.link_button)
        # Concepticon works in any Gloss Language, so it gets its own button instead of a source picker.
        self.link_concept_button = QPushButton("Link Concept…", self)
        self.link_concept_button.setToolTip("Link a Concepticon concept, like the ones in the Swadesh 100")
        self.link_concept_button.clicked.connect(self.link_concept)
        reference_row.addWidget(self.link_concept_button)
        self.unlink_button = QPushButton("Unlink", self)
        self.unlink_button.clicked.connect(self.unlink_sense)
        reference_row.addWidget(self.unlink_button)
        definition_layout.addRow("Concept Reference:", reference_row)
        layout.addLayout(definition_layout)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if entry is not None:
            self.form_input.setText(str(entry.form))
        self.form_warnings.update_form(self.form_input.text())
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
        self._show_reference()

    def _show_reference(self):
        if not 0 <= self._current < len(self._drafts):
            return
        draft = self._drafts[self._current]
        self.reference_label.setText(draft.reference_text())
        self.unlink_button.setEnabled(draft.concept_reference is not None)

    def _lookup(self) -> SenseLookup | None:
        # Getting the lookup doesn't load any data, that waits for the first search.
        return self._senses if self._senses is not None else lookup_for(self.gloss_language)

    def link_sense(self):
        if not 0 <= self._current < len(self._drafts):
            return
        lookup = self._lookup()
        if lookup is None:
            QMessageBox.information(self, "No Dictionary Yet",
                                    f"There's no wordnet to search for the Gloss Language \"{self.gloss_language}\" yet.\n"
                                    "You can still write the Definition without linking a sense, "
                                    "or pick a language with a wordnet in Project Settings.")
            return
        self._link_from(lookup)

    def link_concept(self):
        if not 0 <= self._current < len(self._drafts):
            return
        self._link_from(self._concepts if self._concepts is not None else concepticon_lookup())

    def _link_from(self, lookup: SenseLookup):
        self._store_fields()
        draft = self._drafts[self._current]
        # Start the search with the first Gloss, since that's usually the word you'd look up.
        first_gloss = next((g.strip() for g in draft.glosses if g.strip()), "")
        picker = SensePicker(lookup, first_gloss, self)
        if first_gloss:
            picker.search()
        if picker.exec() == QDialog.DialogCode.Accepted and picker.sense is not None:
            draft.concept_reference = picker.sense.reference
            draft.sense = picker.sense
            self._show_reference()

    def unlink_sense(self):
        if not 0 <= self._current < len(self._drafts):
            return
        draft = self._drafts[self._current]
        draft.concept_reference = None
        draft.sense = None
        self._show_reference()

    def _on_glosses_changed(self):
        # Keep the list label in step with the Glosses as you type.
        if 0 <= self._current < len(self._drafts):
            self._store_fields()
            item = self.definition_list.item(self._current)
            if item is not None:
                item.setText(self._drafts[self._current].label(self._current + 1))

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
        kept: list[Definition] = []
        for draft in self._drafts:
            if draft.definition is None:
                draft.definition = lexicon.add_definition(self.entry, draft.glosses, draft.terms, draft.description)
            else:
                lexicon.edit_definition(self.entry, draft.definition, draft.glosses, draft.terms, draft.description)
            if draft.concept_reference is None:
                lexicon.clear_concept_reference(self.entry, draft.definition)
            else:
                lexicon.set_concept_reference(self.entry, draft.definition, draft.concept_reference)
            kept.append(draft.definition)
        for definition in self.entry.definitions:
            if all(definition is not k for k in kept):
                lexicon.remove_definition(self.entry, definition)
        # After that, put the Definitions in the order they're listed.
        for index, definition in enumerate(kept):
            lexicon.move_definition(self.entry, definition, index)
        # Finally, put on just the checked Tags.
        if self.tag_picker is not None:
            self.tag_picker.apply(lexicon, self.entry)
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
            editor = EntryEditor(self.language, warning.opened, parent=self, gloss_language=self.gloss_language, senses=self._senses, concepts=self._concepts)
            editor.form_warnings.phoneme_added.connect(self.added_phonemes.append)
            editor.exec()
            # The other editor may have added Phonemes, so check this Form again.
            self.form_warnings.update_form(self.form_input.text())
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
        self.match_list.itemDoubleClicked.connect(self.open_match)
        layout.addWidget(self.match_list)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel, self)
        open_button = QPushButton("Open Entry", self)
        open_button.clicked.connect(self.open_match)
        buttons.addButton(open_button, QDialogButtonBox.ButtonRole.ActionRole)
        buttons.addButton("Save Anyway", QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def open_match(self):
        self.opened = self.matches[max(self.match_list.currentRow(), 0)]
        self.reject()

__all__ = ["EntryEditor", "FormWarnings", "HomophoneWarning"]

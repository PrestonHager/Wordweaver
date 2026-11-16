# entry_editor.py

from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QMessageBox, QPlainTextEdit, QWidget

from lexicon import Entry, Form
from wordweaver_project import Language

class EntryEditor(QDialog):
    """A dialog for adding a new Entry to a Language's Lexicon, or editing one that's already there."""

    def __init__(self, language: Language, entry: Entry | None=None, parent: QWidget | None=None):
        super().__init__(parent)
        self.language = language
        self.entry = entry
        self.setWindowTitle("Edit Entry" if entry is not None else "Add Entry")

        layout = QFormLayout(self)
        self.form_input = QLineEdit(self)
        self.form_input.setPlaceholderText("IPA, like kata")
        layout.addRow("Form:", self.form_input)
        self.glosses_input = QPlainTextEdit(self)
        self.glosses_input.setPlaceholderText("One Gloss per line")
        layout.addRow("Glosses:", self.glosses_input)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        if entry is not None:
            self.form_input.setText(str(entry.form))
            self.glosses_input.setPlainText("\n".join(entry.glosses))

    def accept(self):
        # First, split the Form using the Language's Phonemes, so multi-letter ones stay whole.
        form = Form.parse(self.form_input.text(), self.language.inventory.symbols)
        glosses = self.glosses_input.toPlainText().splitlines()
        # Then write it into the Lexicon, and only close if that worked.
        try:
            if self.entry is None:
                self.entry = self.language.lexicon.add(form, glosses)
            else:
                self.language.lexicon.edit(self.entry, form=form, glosses=glosses)
        except ValueError as e:
            QMessageBox.warning(self, "Can't Save Entry", str(e))
            return
        super().accept()

__all__ = ["EntryEditor"]

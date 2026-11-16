# project_settings.py

import re

from PyQt6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLabel, QMessageBox, QVBoxLayout, QWidget

from senses import wordnet_languages
from wordweaver_project import Project, normalize_language_code

# The Gloss Languages that have a wordnet to search. You can also type any other BCP 47 code.
GLOSS_LANGUAGES = tuple(wordnet_languages())

class ProjectSettings(QDialog):
    """A dialog for settings that cover the whole Project, like the Gloss Language."""

    def __init__(self, project: Project, parent: QWidget | None=None):
        super().__init__(parent)
        self.project = project
        self.setWindowTitle("Project Settings")

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        self.gloss_language_input = QComboBox(self)
        self.gloss_language_input.setEditable(True)
        for name, code in GLOSS_LANGUAGES:
            self.gloss_language_input.addItem(f"{name} ({code})")
        self.gloss_language_input.setCurrentText(_label_for(project.gloss_language))
        form_layout.addRow("Gloss Language:", self.gloss_language_input)
        layout.addLayout(form_layout)
        note = QLabel("The language you write Glosses in. It picks which dictionary is searched when you link a sense.\n"
                      "The languages in the list have a wordnet. You can type any other code too, "
                      "but then there's no dictionary to link senses from.", self)
        note.setWordWrap(True)
        layout.addWidget(note)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self):
        # Take the code from "English (en)", or use what was typed as the code.
        text = self.gloss_language_input.currentText()
        match = re.search(r"\(([^()]+)\)\s*$", text)
        try:
            self.project.gloss_language = normalize_language_code(match.group(1) if match else text)
        except ValueError:
            QMessageBox.warning(self, "Can't Save Settings", f"\"{text}\" isn't a language code. Use a code like \"en\" or \"pt-BR\".")
            return
        super().accept()

def _label_for(code: str) -> str:
    return next((f"{name} ({known})" for name, known in GLOSS_LANGUAGES if known == code), code)

__all__ = ["GLOSS_LANGUAGES", "ProjectSettings"]

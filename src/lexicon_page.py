# lexicon_page.py

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QListWidget, QListWidgetItem, QMessageBox, QVBoxLayout, QWidget

import logging

from entry_editor import EntryEditor
from lexicon import Entry
from widgets import Button, Card, EmptyState, PageHeader
from wordweaver_project import Language, Project

class LexiconPage(QWidget):
    """The picked Language's Entries, with buttons to add, edit, and remove them."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Page")
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self.project: Project | None = None
        self.language: Language | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 32)
        layout.setSpacing(16)

        # First, the header with the Add Entry action.
        self.header = PageHeader("Lexicon", "", self)
        add = Button("Add Entry", "plus", "primary", parent=self)
        add.clicked.connect(self.add_entry)
        self.header.add_action(add)
        layout.addWidget(self.header)

        # Then the Entry list in a card, with buttons for the picked Entry under it.
        self.list_card = Card(self)
        self.lexicon_list = QListWidget(self.list_card)
        self.lexicon_list.setObjectName("EntryList")
        self.lexicon_list.itemDoubleClicked.connect(lambda _item: self.edit_entry())
        self.lexicon_list.currentItemChanged.connect(lambda _current, _previous: self._update_buttons())
        self.list_card.layout.addWidget(self.lexicon_list, 1)
        buttons = QHBoxLayout()
        self.edit_button = Button("Edit", "pencil", parent=self.list_card)
        self.edit_button.clicked.connect(self.edit_entry)
        buttons.addWidget(self.edit_button)
        self.remove_button = Button("Remove", "trash-2", "danger", parent=self.list_card)
        self.remove_button.clicked.connect(self.remove_entry)
        buttons.addWidget(self.remove_button)
        buttons.addStretch()
        self.list_card.layout.addLayout(buttons)
        layout.addWidget(self.list_card, 1)

        # Finally, what to show when the Lexicon is empty.
        self.empty = EmptyState("book-open", "No Entries yet",
                                "Add an Entry with its Form and Glosses to start the Lexicon.", self)
        layout.addWidget(self.empty, 1)

    def refresh(self, project: Project | None, language: Language | None):
        self.project = project
        self.language = language
        name = language.name if language is not None else ""
        self.header.subtitle.setText(f"The words in {name}. Double-click an Entry to edit it.")
        self._update_lexicon_list()

    def _update_lexicon_list(self):
        if self.language is None:
            return
        # Show each Entry as its Form and Glosses, and keep its ID on the item to find it again.
        # With Polysemy, number each Definition so you can tell them apart.
        self.lexicon_list.clear()
        for entry in self.language.lexicon:
            meanings = ["; ".join(d.glosses) for d in entry.definitions]
            if len(meanings) > 1:
                meanings = [f"{number}. {meaning}" for number, meaning in enumerate(meanings, start=1)]
            item = QListWidgetItem(f"/{entry.form}/  {'  '.join(meanings)}")
            item.setData(Qt.ItemDataRole.UserRole, entry.id)
            self.lexicon_list.addItem(item)
        # Then swap in the empty state if there's nothing to list.
        has_entries = len(self.language.lexicon) > 0
        self.list_card.setVisible(has_entries)
        self.empty.setVisible(not has_entries)
        self._update_buttons()

    def _update_buttons(self):
        picked = self.lexicon_list.currentItem() is not None
        self.edit_button.setEnabled(picked)
        self.remove_button.setEnabled(picked)

    def _picked_entry(self) -> Entry | None:
        item = self.lexicon_list.currentItem()
        if item is None or self.language is None:
            return None
        return self.language.lexicon.get(item.data(Qt.ItemDataRole.UserRole))

    def add_entry(self):
        if self.language is None:
            return
        editor = EntryEditor(self.language, parent=self)
        if editor.exec() == QDialog.DialogCode.Accepted:
            self._update_lexicon_list()
            self.logger.info(f"Added Entry: {editor.entry}")

    def edit_entry(self):
        entry = self._picked_entry()
        if entry is None:
            return
        if EntryEditor(self.language, entry, parent=self).exec() == QDialog.DialogCode.Accepted:
            self._update_lexicon_list()

    def remove_entry(self):
        entry = self._picked_entry()
        if entry is None:
            return
        answer = QMessageBox.question(self, "Remove Entry", f"Remove /{entry.form}/ ({'; '.join(entry.glosses)})?")
        if answer == QMessageBox.StandardButton.Yes:
            self.language.lexicon.remove(entry)
            self._update_lexicon_list()
            self.logger.info(f"Removed Entry: {entry}")

__all__ = ["LexiconPage"]

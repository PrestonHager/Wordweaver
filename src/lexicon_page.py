# lexicon_page.py

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QCheckBox, QComboBox, QDialog, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QVBoxLayout, QWidget

import logging

from entry_editor import EntryEditor
from lexicon import Entry, SearchField, SortOrder
from tag_widgets import TagFilter, TagManager
from widgets import Button, Card, EmptyState, PageHeader, label
from wordweaver_project import Language, Project

class LexiconPage(QWidget):
    """The picked Language's Entries, with buttons to add, edit, and remove them."""

    # Sent when the Entry editor adds a Phoneme to the Inventory from a Form warning.
    inventory_changed = pyqtSignal()  # pyright: ignore[reportCallIssue]  PyQt6 stub bug, see pyproject.

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)  # pyright: ignore[reportArgumentType]  PyQt6 stub bug, see pyproject.
        self.setObjectName("Page")
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)
        self.project: Project | None = None
        self.language: Language | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 32)
        layout.setSpacing(16)

        # First, the header with the Tag manager and Add Entry actions.
        self.header = PageHeader("Lexicon", "", self)
        manage_tags = Button("Manage Tags", "pencil", parent=self)
        manage_tags.clicked.connect(self.manage_tags)
        self.header.add_action(manage_tags)
        add = Button("Add Entry", "plus", "primary", parent=self)
        add.clicked.connect(self.add_entry)
        self.header.add_action(add)
        layout.addWidget(self.header)

        # Then the Entry list in a card, with buttons for the picked Entry under it.
        self.list_card = Card(self)
        # The search box and Tag filter sit on top, so you can work on one group of words at a time.
        toolbar = QHBoxLayout()
        self.search_box = QLineEdit(self.list_card)
        self.search_box.setPlaceholderText("Search")
        self.search_box.setClearButtonEnabled(True)
        self.search_box.textChanged.connect(self._update_lexicon_list)
        toolbar.addWidget(self.search_box, 1)
        self.search_field_picker = QComboBox(self.list_card)
        for field in SearchField:
            self.search_field_picker.addItem(str(field), field)
        self.search_field_picker.setCurrentIndex(list(SearchField).index(SearchField.GLOSS))
        self.search_field_picker.currentIndexChanged.connect(self._update_lexicon_list)
        toolbar.addWidget(self.search_field_picker)
        toolbar.addSpacing(8)
        toolbar.addWidget(label("Tag", "muted", self.list_card))
        self.tag_filter = TagFilter(self.list_card)
        self.tag_filter.setMinimumWidth(160)
        self.tag_filter.currentIndexChanged.connect(self._update_lexicon_list)
        toolbar.addWidget(self.tag_filter)
        toolbar.addSpacing(8)
        # Unfinished Entries have no Form yet, like the ones seeded from a concept list.
        self.unfinished_filter = QCheckBox("Unfinished only", self.list_card)
        self.unfinished_filter.setToolTip("Only show Entries that don't have a Form yet")
        self.unfinished_filter.toggled.connect(self._update_lexicon_list)
        toolbar.addWidget(self.unfinished_filter)
        toolbar.addSpacing(8)
        toolbar.addWidget(label("Sort", "muted", self.list_card))
        self.sort_picker = QComboBox(self.list_card)
        for order in SortOrder:
            self.sort_picker.addItem(str(order), order)
        self.sort_picker.currentIndexChanged.connect(self._update_lexicon_list)
        toolbar.addWidget(self.sort_picker)
        self.list_card.content.addLayout(toolbar)
        self.lexicon_list = QListWidget(self.list_card)
        self.lexicon_list.setObjectName("EntryList")
        self.lexicon_list.itemDoubleClicked.connect(self.edit_entry)
        self.lexicon_list.currentItemChanged.connect(self._update_buttons)
        self.list_card.content.addWidget(self.lexicon_list, 1)
        buttons = QHBoxLayout()
        self.edit_button = Button("Edit", "pencil", parent=self.list_card)
        self.edit_button.clicked.connect(self.edit_entry)
        buttons.addWidget(self.edit_button)
        self.remove_button = Button("Remove", "trash-2", "danger", parent=self.list_card)
        self.remove_button.clicked.connect(self.remove_entry)
        buttons.addWidget(self.remove_button)
        buttons.addStretch()
        self.list_card.content.addLayout(buttons)
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
        if self.project is None or self.language is None:
            return
        # First, refill the Tag filter, since Tags can change from the editor or the Tag manager.
        self.tag_filter.refresh(self.project.tags)
        tag = self.tag_filter.picked_tag(self.project.tags)
        # Now search inside that Tag, and let the Lexicon decide the order.
        entries = self.language.lexicon.search(self.search_box.text(), self.search_field_picker.currentData(), tag=tag, sort=self.sort_picker.currentData())
        # Next, keep only the unfinished Entries, if that's ticked.
        if self.unfinished_filter.isChecked():
            entries = [entry for entry in entries if entry.is_unfinished]
        # Then show each Entry as its Form, Glosses, and Tags, and keep its ID on the item to find it again.
        # With Polysemy, number each Definition so you can tell them apart.
        self.lexicon_list.clear()
        for entry in entries:
            meanings = ["; ".join(d.glosses) for d in entry.definitions]
            if len(meanings) > 1:
                meanings = [f"{number}. {meaning}" for number, meaning in enumerate(meanings, start=1)]
            form = "(no Form yet)" if entry.is_unfinished else f"/{entry.form}/"
            text = f"{form}  {'  '.join(meanings)}"
            tag_names = [tag.name for tag_id in entry.tag_ids if (tag := self.project.tags.get(tag_id)) is not None]
            if tag_names:
                text += f"  [{', '.join(tag_names)}]"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, entry.id)
            self.lexicon_list.addItem(item)
        # Finally, swap in the empty state if the Lexicon has nothing in it at all.
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
        if self.project is None or self.language is None:
            return
        editor = EntryEditor(self.language, parent=self, gloss_language=self.project.gloss_language)
        accepted = editor.exec() == QDialog.DialogCode.Accepted
        # Refresh either way, since the Homophone warning can open and change another Entry.
        self._update_lexicon_list()
        self._check_inventory(editor)
        if accepted:
            self.logger.info(f"Added Entry: {editor.entry}")

    def edit_entry(self):
        entry = self._picked_entry()
        if entry is None or self.project is None or self.language is None:
            return
        editor = EntryEditor(self.language, entry, parent=self, gloss_language=self.project.gloss_language)
        editor.exec()
        self._update_lexicon_list()
        self._check_inventory(editor)

    def _check_inventory(self, editor: EntryEditor):
        # Phonemes added from the Form warnings stay even if the editor was cancelled.
        if editor.added_phonemes:
            self.logger.info(f"Added Phonemes from the Lexicon: {', '.join(editor.added_phonemes)}")
            self.inventory_changed.emit()

    def remove_entry(self):
        entry = self._picked_entry()
        if entry is None or self.language is None:
            return
        answer = QMessageBox.question(self, "Remove Entry", f"Remove /{entry.form}/ ({'; '.join(entry.glosses)})?")
        if answer == QMessageBox.StandardButton.Yes:
            self.language.lexicon.remove(entry)
            self._update_lexicon_list()
            self.logger.info(f"Removed Entry: {entry}")

    def manage_tags(self):
        if self.project is None:
            return
        TagManager(self.project, parent=self).exec()
        self._update_lexicon_list()

__all__ = ["LexiconPage"]

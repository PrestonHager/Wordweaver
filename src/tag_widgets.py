# tag_widgets.py

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QHBoxLayout, QInputDialog, QListWidget, QListWidgetItem, QMessageBox, QVBoxLayout, QWidget

from lexicon import Entry, Lexicon
from tags import Tag, Tags
from widgets import Button
from wordweaver_project import Project

def _sorted(tags: Tags) -> list[Tag]:
    return sorted(tags, key=lambda tag: tag.name.casefold())

def _ask_new_tag(tags: Tags, parent: QWidget) -> Tag | None:
    # Keep asking until we get a name that works, or the user gives up.
    name = ""
    while True:
        name, ok = QInputDialog.getText(parent, "New Tag", "Enter a name for the new Tag:", text=name)
        if not ok:
            return None
        try:
            return tags.add(name)
        except ValueError as e:
            QMessageBox.warning(parent, "Can't Add Tag", str(e))

class TagManager(QDialog):
    """A dialog for adding, renaming, and removing the Project's Tags."""

    def __init__(self, project: Project, parent: QWidget | None=None):
        super().__init__(parent)
        self.project = project
        self.setWindowTitle("Manage Tags")

        layout = QVBoxLayout(self)
        self.tag_list = QListWidget(self)
        self.tag_list.itemDoubleClicked.connect(lambda _item: self.rename_tag())
        layout.addWidget(self.tag_list)
        buttons = QWidget(self)
        buttons_layout = QHBoxLayout(buttons)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        for text, icon, variant, slot in (("Add", "plus", None, self.add_tag), ("Rename", "pencil", None, self.rename_tag),
                                          ("Remove", "trash-2", "danger", self.remove_tag)):
            button = Button(text, icon, variant, parent=buttons)
            button.clicked.connect(slot)
            buttons_layout.addWidget(button)
        buttons_layout.addStretch()
        layout.addWidget(buttons)
        close_button = QDialogButtonBox(QDialogButtonBox.StandardButton.Close, self)
        close_button.rejected.connect(self.accept)
        layout.addWidget(close_button)

        self._update_tag_list()

    def _update_tag_list(self):
        # Show each Tag with how many Entries have it, across every Language.
        self.tag_list.clear()
        for tag in _sorted(self.project.tags):
            item = QListWidgetItem(f"{tag.name}  ({len(self.project.tagged(tag))})")
            item.setData(Qt.ItemDataRole.UserRole, tag.id)
            self.tag_list.addItem(item)

    def _picked_tag(self) -> Tag | None:
        item = self.tag_list.currentItem()
        if item is None:
            return None
        return self.project.tags.get(item.data(Qt.ItemDataRole.UserRole))

    def add_tag(self):
        if _ask_new_tag(self.project.tags, self) is not None:
            self._update_tag_list()

    def rename_tag(self):
        tag = self._picked_tag()
        if tag is None:
            return
        name, ok = QInputDialog.getText(self, "Rename Tag", "Enter a new name for the Tag:", text=tag.name)
        if not ok:
            return
        try:
            self.project.tags.rename(tag, name)
        except ValueError as e:
            QMessageBox.warning(self, "Can't Rename Tag", str(e))
            return
        self._update_tag_list()

    def remove_tag(self):
        tag = self._picked_tag()
        if tag is None:
            return
        count = len(self.project.tagged(tag))
        answer = QMessageBox.question(self, "Remove Tag", f"Remove {tag.name!r}? It will be taken off {count} Entries in every Language.")
        if answer == QMessageBox.StandardButton.Yes:
            self.project.tags.remove(tag)
            self._update_tag_list()

class TagPicker(QWidget):
    """A checklist of the Project's Tags, for picking which ones go on an Entry."""

    def __init__(self, tags: Tags, entry: Entry | None=None, parent: QWidget | None=None):
        super().__init__(parent)  # pyright: ignore[reportArgumentType]  PyQt6 stub bug, see pyproject.
        self.tags = tags

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.tag_list = QListWidget(self)
        self.tag_list.setMaximumHeight(120)
        layout.addWidget(self.tag_list)
        new_button = Button("New Tag", "plus", parent=self)
        new_button.clicked.connect(self.new_tag)
        layout.addWidget(new_button, 0, Qt.AlignmentFlag.AlignLeft)

        checked = set(entry.tag_ids) if entry is not None else set()
        for tag in _sorted(tags):
            self._add_item(tag, tag.id in checked)

    def _add_item(self, tag: Tag, checked: bool):
        item = QListWidgetItem(tag.name)
        item.setData(Qt.ItemDataRole.UserRole, tag.id)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        self.tag_list.addItem(item)

    def new_tag(self):
        # A new Tag is made right away, and starts out checked since you probably want it on this Entry.
        tag = _ask_new_tag(self.tags, self)
        if tag is not None:
            self._add_item(tag, True)

    def checked_tags(self) -> list[Tag]:
        checked = []
        for i in range(self.tag_list.count()):
            item = self.tag_list.item(i)
            if item is None or item.checkState() != Qt.CheckState.Checked:
                continue
            tag = self.tags.get(item.data(Qt.ItemDataRole.UserRole))
            if tag is not None:
                checked.append(tag)
        return checked

    def apply(self, lexicon: Lexicon, entry: Entry):
        """Tag and untag `entry` so it has just the checked Tags."""
        checked = self.checked_tags()
        for tag_id in entry.tag_ids:
            tag = self.tags.get(tag_id)
            if tag is not None and tag not in checked:
                lexicon.untag(entry, tag)
        for tag in checked:
            lexicon.tag(entry, tag)

class TagFilter(QComboBox):
    """A drop-down for showing only the Entries with one Tag, or every Entry."""

    def __init__(self, parent: QWidget | None=None):
        super().__init__(parent)
        self.addItem("All Entries", None)

    def refresh(self, tags: Tags):
        # Refill the list, keeping the picked Tag if it's still there.
        picked = self.currentData()
        self.blockSignals(True)
        self.clear()
        self.addItem("All Entries", None)
        for tag in _sorted(tags):
            self.addItem(tag.name, tag.id)
        index = self.findData(picked)
        self.setCurrentIndex(index if index >= 0 else 0)
        self.blockSignals(False)

    def picked_tag(self, tags: Tags) -> Tag | None:
        tag_id = self.currentData()
        return tags.get(tag_id) if tag_id is not None else None

__all__ = ["TagFilter", "TagManager", "TagPicker"]

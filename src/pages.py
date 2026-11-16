# pages.py
#
# The Welcome, Overview, and Lexicon pages. Phonology has its own file since it's bigger.

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QComboBox, QFrame, QHBoxLayout, QScrollArea, QVBoxLayout, QWidget

from widgets import Button, Card, EmptyState, FlowLayout, PageHeader, label
from wordweaver_project import Language, LanguageKind, Project

# How many symbols a Language card shows before cutting off.
PREVIEW_SYMBOLS = 18

class WelcomePage(QWidget):
    """What you see with no Project open."""

    new_requested = pyqtSignal()
    open_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Welcome")
        layout = QVBoxLayout(self)
        layout.addStretch(2)
        column = QVBoxLayout()
        column.setSpacing(8)
        hero = label("Wordweaver", "hero", self)
        hero.setAlignment(Qt.AlignmentFlag.AlignCenter)
        column.addWidget(hero)
        tagline = label("A toolbox for building constructed languages.", "subtitle", self)
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        column.addWidget(tagline)
        column.addSpacing(28)
        buttons = QHBoxLayout()
        buttons.setSpacing(16)
        buttons.addStretch()
        new = Button("New Project\nStart fresh with one Language", "file-plus", "big", parent=self, icon_size=26)
        new.clicked.connect(self.new_requested)
        open_ = Button("Open Project\nPick up a .wwproj file", "folder-open", "big", parent=self, icon_size=26)
        open_.clicked.connect(self.open_requested)
        for button in (new, open_):
            button.setMinimumWidth(260)
            buttons.addWidget(button)
        buttons.addStretch()
        column.addLayout(buttons)
        layout.addLayout(column)
        layout.addStretch(3)

class LanguageCard(Card):
    """One Language on the Overview, with its kind, a preview of its sounds, and actions."""

    def __init__(self, language: Language, current: bool, page: "OverviewPage"):
        super().__init__(page, padding=16, spacing=10)
        self.setFixedWidth(300)
        # First the name, with a badge on the one being edited.
        top = QHBoxLayout()
        top.addWidget(label(language.name, "cardTitle"), 1)
        if current:
            top.addWidget(label("Editing", "badge"))
        self.layout.addLayout(top)
        # Then the Language Kind picker.
        kind = QComboBox(self)
        for k in LanguageKind:
            kind.addItem(str(k))
        kind.setCurrentIndex(list(LanguageKind).index(language.kind))
        kind.currentIndexChanged.connect(lambda i: page.kind_changed.emit(language, list(LanguageKind)[i]))
        self.layout.addWidget(kind)
        # Now a peek at the Phoneme Inventory.
        symbols = language.inventory.symbols
        count = f"{len(symbols)} Phoneme" + ("" if len(symbols) == 1 else "s")
        self.layout.addWidget(label(count, "muted"))
        preview = " ".join(symbols[:PREVIEW_SYMBOLS]) + (" …" if len(symbols) > PREVIEW_SYMBOLS else "")
        sounds = label(preview or "No sounds yet", "ipa" if symbols else "muted")
        sounds.setWordWrap(True)
        self.layout.addWidget(sounds)
        self.layout.addStretch()
        # Finally the actions.
        actions = QHBoxLayout()
        phonology = Button("Phonology", "audio-lines", parent=self)
        phonology.clicked.connect(lambda: page.phonology_requested.emit(language))
        actions.addWidget(phonology)
        actions.addStretch()
        rename = Button(icon="pencil", variant="ghost", tooltip="Rename Language", parent=self)
        rename.clicked.connect(lambda: page.rename_requested.emit(language))
        actions.addWidget(rename)
        remove = Button(icon="trash-2", variant="danger", tooltip="Remove Language", parent=self)
        remove.clicked.connect(lambda: page.remove_requested.emit(language))
        actions.addWidget(remove)
        self.layout.addLayout(actions)

class OverviewPage(QWidget):
    """The Project at a glance: every Language as a card."""

    add_requested = pyqtSignal()
    rename_project_requested = pyqtSignal()
    phonology_requested = pyqtSignal(object)
    rename_requested = pyqtSignal(object)
    remove_requested = pyqtSignal(object)
    kind_changed = pyqtSignal(object, object)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Page")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll)
        body = QWidget(scroll)
        scroll.setWidget(body)
        layout = QVBoxLayout(body)
        layout.setContentsMargins(32, 28, 32, 32)
        layout.setSpacing(20)

        self.header = PageHeader("Untitled Project", "", body)
        rename = Button("Rename", "pencil", parent=body)
        rename.clicked.connect(self.rename_project_requested)
        self.header.add_action(rename)
        add = Button("Add Language", "plus", "primary", parent=body)
        add.clicked.connect(self.add_requested)
        self.header.add_action(add)
        layout.addWidget(self.header)

        layout.addWidget(label("LANGUAGES", "section"))
        self.cards_box = QWidget(body)
        self.cards = FlowLayout(self.cards_box, spacing=16)
        layout.addWidget(self.cards_box)
        layout.addStretch()

    def refresh(self, project: Project, current: Language | None):
        self.header.title.setText(project.name)
        count = len(project.languages)
        self.header.subtitle.setText(f"{count} Language" + ("" if count == 1 else "s") + " in this Project.")
        self.cards.clear()
        for language in project.languages:
            self.cards.addWidget(LanguageCard(language, language is current, self))
        # The last card is a big dashed button for adding another Language.
        add = Button("Add a Language", "plus", "dashed", parent=self.cards_box)
        add.setFixedSize(300, 200)
        add.clicked.connect(self.add_requested)
        self.cards.addWidget(add)

class LexiconPage(QWidget):
    """A placeholder until Languages have a Lexicon."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Page")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 32)
        layout.addWidget(PageHeader("Lexicon", "The words in this Language.", self))
        layout.addWidget(EmptyState("book-open", "The Lexicon is on its way",
                                    "Soon you'll add Entries here, with their forms and Definitions.", self), 1)

__all__ = ["WelcomePage", "OverviewPage", "LexiconPage"]

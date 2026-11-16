# widgets.py
#
# Small building blocks every page shares, so the app looks the same everywhere.

from PyQt6.QtCore import QPoint, QRect, QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLayout, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from icons import bind_icon

# Which theme color an icon gets on each kind of button.
ICON_COLORS = {
    "primary": ("accent_text", None),
    "nav": ("muted", "accent"),
    "danger": ("danger", None),
    "dashed": ("muted", None),
}

def label(text: str, role: str | None = None, parent: QWidget | None = None) -> QLabel:
    # Make a label with one of the stylesheet's roles, like "title" or "muted".
    result = QLabel(text, parent)
    if role is not None:
        result.setProperty("role", role)
    return result

class Button(QPushButton):
    """A push button with an optional Lucide icon and a style variant.

    Variants are "primary", "ghost", "danger", "nav", "big", "dashed", or None for a plain button.
    """

    def __init__(self, text: str = "", icon: str | None = None, variant: str | None = None,
                 tooltip: str | None = None, parent: QWidget | None = None, icon_size: int = 18,
                 icon_color: str | None = None):
        super().__init__(text, parent)
        if variant is not None:
            self.setProperty("variant", variant)
        if tooltip:
            self.setToolTip(tooltip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if icon is not None:
            color, checked = ICON_COLORS.get(variant, ("text", None))
            color = icon_color or color
            bind_icon(self, icon, color, checked, icon_size)
            self.setIconSize(QSize(icon_size, icon_size))
        # Icon-only buttons are square.
        if icon is not None and not text:
            self.setFixedSize(32, 32)

class Card(QFrame):
    """A rounded panel on the surface color."""

    def __init__(self, parent: QWidget | None = None, padding: int = 16, spacing: int = 12):
        super().__init__(parent)
        self.setProperty("card", True)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(padding, padding, padding, padding)
        self.layout.setSpacing(spacing)

class PageHeader(QWidget):
    """A page title with a subtitle under it and actions on the right."""

    def __init__(self, title: str, subtitle: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        text = QVBoxLayout()
        text.setSpacing(2)
        self.title = label(title, "title")
        self.subtitle = label(subtitle, "subtitle")
        self.subtitle.setWordWrap(True)
        text.addWidget(self.title)
        text.addWidget(self.subtitle)
        layout.addLayout(text, 1)
        self.actions = QHBoxLayout()
        self.actions.setSpacing(6)
        layout.addLayout(self.actions)

    def add_action(self, widget: QWidget):
        self.actions.addWidget(widget, 0, Qt.AlignmentFlag.AlignTop)

class Chip(QFrame):
    """A small rounded tag with a remove button, used for Phonemes in an inventory."""

    removed = pyqtSignal(str)

    def __init__(self, text: str, tooltip: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Chip")
        self.setFixedHeight(28)
        self.text = text
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 2, 4, 2)
        layout.setSpacing(2)
        layout.addWidget(QLabel(text, self))
        if tooltip:
            self.setToolTip(tooltip)
        remove = Button(icon="x", tooltip=f"Remove {text}", parent=self, icon_size=14)
        remove.setFixedSize(20, 20)
        remove.clicked.connect(lambda: self.removed.emit(self.text))
        layout.addWidget(remove)

class FlowLayout(QLayout):
    """Lays widgets out left to right and wraps them onto new rows, like words in a paragraph."""

    def __init__(self, parent: QWidget | None = None, spacing: int = 6):
        super().__init__(parent)
        self._items = []
        self.setSpacing(spacing)
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if 0 <= index < len(self._items) else None

    def takeAt(self, index):
        return self._items.pop(index) if 0 <= index < len(self._items) else None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._arrange(QRect(0, 0, width, 0), move=False)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._arrange(rect, move=True)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        return size + QSize(margins.left() + margins.right(), margins.top() + margins.bottom())

    def clear(self):
        # Remove and delete every widget in the layout.
        while self._items:
            item = self._items.pop()
            if item.widget() is not None:
                item.widget().deleteLater()

    def _arrange(self, rect: QRect, move: bool) -> int:
        # Walk the items, starting a new row whenever the next one won't fit.
        x, y, row_height = rect.x(), rect.y(), 0
        gap = self.spacing()
        for item in self._items:
            hint = item.sizeHint()
            if x + hint.width() > rect.right() and row_height > 0:
                x = rect.x()
                y += row_height + gap
                row_height = 0
            if move:
                item.setGeometry(QRect(QPoint(x, y), hint))
            x += hint.width() + gap
            row_height = max(row_height, hint.height())
        return y + row_height - rect.y()

class EmptyState(QWidget):
    """A centered message for a page with nothing on it yet."""

    def __init__(self, icon_name: str, title: str, text: str, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addStretch()
        badge = Button(icon=icon_name, variant="ghost", parent=self, icon_size=40, icon_color="muted")
        badge.setFixedSize(72, 72)
        badge.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignHCenter)
        heading = label(title, "cardTitle", self)
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(heading)
        body = label(text, "muted", self)
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.setWordWrap(True)
        body.setMaximumWidth(420)
        layout.addWidget(body, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()

def hline(parent: QWidget | None = None) -> QFrame:
    # A thin divider line.
    line = QFrame(parent)
    line.setFixedHeight(1)
    line.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    line.setProperty("card", True)
    return line

__all__ = ["Button", "Card", "Chip", "EmptyState", "FlowLayout", "PageHeader", "label", "hline"]

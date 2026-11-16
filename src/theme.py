# theme.py

from pathlib import Path
from platformdirs import user_cache_path
from PyQt6.QtCore import QObject, QSettings, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QGuiApplication, QPalette
from PyQt6.QtWidgets import QApplication

# The colors every widget pulls from. Keep new UI on these tokens instead of hard-coded colors.
LIGHT = {
    "bg": "#f6f6f8",
    "surface": "#ffffff",
    "sidebar": "#efeff3",
    "border": "#e1e1e8",
    "text": "#1c1c22",
    "muted": "#6c6c78",
    "accent": "#5b5bd6",
    "accent_text": "#ffffff",
    "accent_soft": "#e9e9fb",
    "hover": "#e6e6ec",
    "danger": "#cf3b3b",
    "danger_soft": "#fbeaea",
}
DARK = {
    "bg": "#18181c",
    "surface": "#212126",
    "sidebar": "#131316",
    "border": "#303038",
    "text": "#ececf1",
    "muted": "#9b9ba8",
    "accent": "#7d7df2",
    "accent_text": "#ffffff",
    "accent_soft": "#2b2b4d",
    "hover": "#2c2c33",
    "danger": "#f06a6a",
    "danger_soft": "#3a2226",
}

# Segoe UI and Noto Sans both cover the IPA, so phoneme symbols draw from one font.
UI_FONTS = '"Segoe UI Variable Text", "Segoe UI", "Inter", "Noto Sans", sans-serif'
IPA_FONTS = '"Segoe UI", "Noto Sans", "DejaVu Sans", "Charis SIL", sans-serif'

STYLESHEET = """
QWidget {{ color: {text}; font-size: 13px; font-family: {ui_fonts}; }}
QMainWindow, QWidget#Page, QWidget#Welcome {{ background: {bg}; }}
QScrollArea, QScrollArea > QWidget > QWidget {{ background: transparent; border: none; }}
QToolTip {{ background: {surface}; color: {text}; border: 1px solid {border}; padding: 4px 8px; border-radius: 6px; }}

QWidget#Sidebar {{ background: {sidebar}; border-right: 1px solid {border}; }}
QLabel#AppName {{ font-size: 17px; font-weight: 700; }}

QLabel[role="title"] {{ font-size: 24px; font-weight: 700; }}
QLabel[role="hero"] {{ font-size: 40px; font-weight: 800; }}
QLabel[role="subtitle"], QLabel[role="muted"] {{ color: {muted}; }}
QLabel[role="section"] {{ color: {muted}; font-size: 11px; font-weight: 700; letter-spacing: 1px; }}
QLabel[role="cardTitle"] {{ font-size: 15px; font-weight: 600; }}
QLabel[role="badge"] {{ background: {accent_soft}; color: {accent}; border-radius: 8px; padding: 2px 8px; font-size: 11px; font-weight: 600; }}
QLabel[role="error"] {{ color: {danger}; }}
QLabel[role="axis"] {{ color: {muted}; font-size: 11px; }}
QLabel[role="ipa"] {{ font-family: {ipa_fonts}; font-size: 16px; color: {text}; }}
QLabel[role="position"] {{ background: {accent_soft}; color: {accent}; border: 1px solid {accent_soft}; border-radius: 6px; padding: 4px 10px; font-size: 15px; font-weight: 600; }}
QLabel[role="position"][optional="true"] {{ background: transparent; color: {muted}; border: 1px dashed {muted}; }}

QFrame[card="true"] {{ background: {surface}; border: 1px solid {border}; border-radius: 12px; }}
QFrame#ChartCell {{ border: none; border-right: 1px solid {border}; border-bottom: 1px solid {border}; background: transparent; }}

QPushButton {{ background: {surface}; border: 1px solid {border}; border-radius: 8px; padding: 6px 12px; }}
QPushButton:hover {{ background: {hover}; }}
QPushButton:pressed {{ background: {border}; }}
QPushButton:disabled {{ color: {muted}; }}
QPushButton[variant="primary"] {{ background: {accent}; color: {accent_text}; border-color: {accent}; font-weight: 600; }}
QPushButton[variant="primary"]:hover {{ background: {accent}; border-color: {text}; }}
QPushButton[variant="primary"]:disabled {{ background: {border}; border-color: {border}; color: {muted}; }}
QPushButton[variant="ghost"] {{ background: transparent; border-color: transparent; }}
QPushButton[variant="ghost"]:hover {{ background: {hover}; }}
QPushButton[variant="danger"] {{ background: transparent; border-color: transparent; color: {danger}; }}
QPushButton[variant="danger"]:hover {{ background: {danger_soft}; }}
QPushButton[variant="nav"] {{ background: transparent; border: none; text-align: left; padding: 8px 10px; color: {muted}; font-weight: 500; }}
QPushButton[variant="nav"]:hover {{ background: {hover}; color: {text}; }}
QPushButton[variant="nav"]:checked {{ background: {accent_soft}; color: {accent}; font-weight: 600; }}
QPushButton[variant="big"] {{ padding: 18px 22px; border-radius: 12px; font-size: 15px; font-weight: 600; text-align: left; }}
QPushButton[variant="big"]:hover {{ border-color: {accent}; }}
QPushButton[variant="dashed"] {{ background: transparent; border: 2px dashed {border}; border-radius: 12px; color: {muted}; font-weight: 600; }}
QPushButton[variant="dashed"]:hover {{ border-color: {accent}; color: {accent}; }}

QPushButton#Phoneme {{ font-family: {ipa_fonts}; font-size: 18px; padding: 0; border-radius: 8px; background: {surface}; }}
QPushButton#Phoneme:hover {{ border-color: {accent}; }}
QPushButton#Phoneme:checked {{ background: {accent}; color: {accent_text}; border-color: {accent}; }}

QFrame#Chip {{ background: {accent_soft}; border-radius: 13px; }}
QFrame#Chip QLabel {{ color: {accent}; font-family: {ipa_fonts}; font-size: 16px; background: transparent; }}
QFrame#Chip QLabel#ChipDetail {{ color: {muted}; font-size: 13px; padding-left: 4px; }}
QFrame#Chip QPushButton {{ background: transparent; border: none; padding: 0; border-radius: 9px; }}
QFrame#Chip QPushButton:hover {{ background: {hover}; }}

QLineEdit, QComboBox {{ background: {surface}; border: 1px solid {border}; border-radius: 8px; padding: 6px 10px; selection-background-color: {accent}; selection-color: {accent_text}; }}
QLineEdit:focus, QComboBox:focus {{ border-color: {accent}; }}
QLineEdit[invalid="true"] {{ border-color: {danger}; }}
QLineEdit#IpaInput {{ font-family: {ipa_fonts}; font-size: 15px; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox::down-arrow {{ image: url("{chevron}"); width: 14px; height: 14px; }}
QComboBox QAbstractItemView {{ background: {surface}; border: 1px solid {border}; selection-background-color: {accent_soft}; selection-color: {text}; outline: none; padding: 4px; }}

QCheckBox {{ spacing: 8px; background: transparent; }}
QCheckBox::indicator {{ width: 16px; height: 16px; border: 1px solid {muted}; border-radius: 4px; background: {surface}; }}
QCheckBox::indicator:hover {{ border-color: {accent}; }}
QCheckBox::indicator:checked {{ background: {accent}; border-color: {accent}; image: url("{check}"); }}
QCheckBox::indicator:disabled {{ border-color: {border}; background: {bg}; }}

QListWidget#EntryList {{ background: transparent; border: none; outline: none; font-size: 14px; }}
QListWidget#EntryList::item {{ padding: 8px 10px; border-radius: 8px; }}
QListWidget#EntryList::item:hover {{ background: {hover}; }}
QListWidget#EntryList::item:selected {{ background: {accent_soft}; color: {text}; }}

QMenuBar {{ background: {bg}; border-bottom: 1px solid {border}; }}
QMenuBar::item {{ padding: 6px 10px; background: transparent; border-radius: 6px; }}
QMenuBar::item:selected {{ background: {hover}; }}
QMenu {{ background: {surface}; border: 1px solid {border}; border-radius: 8px; padding: 4px; }}
QMenu::item {{ padding: 6px 24px 6px 10px; border-radius: 6px; }}
QMenu::item:selected {{ background: {accent_soft}; color: {text}; }}
QMenu::item:disabled {{ color: {muted}; }}
QMenu::separator {{ height: 1px; background: {border}; margin: 4px 6px; }}
QMenu::icon {{ padding-left: 8px; }}

QStatusBar {{ background: {bg}; color: {muted}; border-top: 1px solid {border}; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {border}; border-radius: 4px; min-height: 30px; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {border}; border-radius: 4px; min-width: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page {{ background: none; border: none; width: 0; height: 0; }}
"""

def _tinted_icon(name: str, color: str) -> str:
    # Stylesheets can only load images from files, so write a tinted copy of the icon to the cache folder.
    source = Path(__file__).parent / "icons" / "lucide" / f"{name}.svg"
    target = user_cache_path("Wordweaver", False, ensure_exists=True) / f"{name}-{color.lstrip('#')}.svg"
    if not target.exists():
        target.write_bytes(source.read_bytes().replace(b"currentColor", color.encode()))
    return target.as_posix()

class Theme(QObject):
    """Holds the light or dark palette and tells widgets when it changes."""

    changed = pyqtSignal()  # pyright: ignore[reportCallIssue]  PyQt6 stub bug, see pyproject.

    def __init__(self):
        super().__init__()  # pyright: ignore[reportArgumentType]  PyQt6 stub bug, see pyproject.
        # The mode is "system", "light", or "dark", and it's remembered between runs.
        self._settings = QSettings("Wordweaver", "Wordweaver")
        self.mode = str(self._settings.value("theme", "system"))
        self.colors = LIGHT

    @property
    def is_dark(self) -> bool:
        return self.colors is DARK

    def color(self, token: str) -> str:
        return self.colors[token]

    def apply(self, app: QApplication):
        # First, figure out which palette we want.
        if self.mode == "system":
            hints = QGuiApplication.styleHints()
            dark = hints is not None and hints.colorScheme() == Qt.ColorScheme.Dark
        else:
            dark = self.mode == "dark"
        self.colors = DARK if dark else LIGHT
        # Now set Fusion and a matching palette, so anything the stylesheet misses still fits.
        app.setStyle("Fusion")
        palette = QPalette()
        c = self.colors
        for role, token in ((QPalette.ColorRole.Window, "bg"), (QPalette.ColorRole.Base, "surface"),
                            (QPalette.ColorRole.AlternateBase, "bg"), (QPalette.ColorRole.Button, "surface"),
                            (QPalette.ColorRole.Text, "text"), (QPalette.ColorRole.WindowText, "text"),
                            (QPalette.ColorRole.ButtonText, "text"), (QPalette.ColorRole.Highlight, "accent"),
                            (QPalette.ColorRole.HighlightedText, "accent_text"), (QPalette.ColorRole.ToolTipBase, "surface"),
                            (QPalette.ColorRole.ToolTipText, "text"), (QPalette.ColorRole.PlaceholderText, "muted")):
            palette.setColor(role, QColor(c[token]))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(c["muted"]))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(c["muted"]))
        app.setPalette(palette)
        # Finally, the stylesheet, then let the widgets re-tint their icons.
        app.setStyleSheet(STYLESHEET.format(ipa_fonts=IPA_FONTS, ui_fonts=UI_FONTS, chevron=_tinted_icon("chevron-down", c["muted"]), check=_tinted_icon("check", c["accent_text"]), **c))
        self.changed.emit()

    def toggle(self, app: QApplication):
        # Flip to the opposite of what's showing, and stop following the system.
        self.mode = "light" if self.is_dark else "dark"
        self._settings.setValue("theme", self.mode)
        self.apply(app)

    def follow_system(self, app: QApplication):
        # Re-apply when the system scheme changes, but only if we're following it.
        def on_change():
            if self.mode == "system":
                self.apply(app)
        hints = QGuiApplication.styleHints()
        if hints is not None:
            hints.colorSchemeChanged.connect(on_change)

# There's one theme for the whole app.
theme = Theme()

__all__ = ["theme", "Theme", "LIGHT", "DARK"]

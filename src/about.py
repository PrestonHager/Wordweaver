# about.py

from PyQt6.QtWidgets import QDialog, QHBoxLayout, QMainWindow, QVBoxLayout
from pathlib import Path

from widgets import Button, label

with open(Path(__file__).parent.joinpath(Path("VERSION")), "r") as f:
    VERSION = f.read().strip()
GITHUB_URL = "https://github.com/PrestonHager/Wordweaver"

class About(QDialog):
    def __init__(self, parent: QMainWindow):
        super().__init__(parent)

        self.setWindowTitle("About Wordweaver")
        self.setMinimumWidth(380)

        self.content = QVBoxLayout(self)
        self.content.setContentsMargins(24, 24, 24, 20)
        self.content.setSpacing(6)
        self.content.addWidget(label("Wordweaver", "title", self))
        self.content.addWidget(label(f"Version {VERSION}", "muted", self))
        self.content.addSpacing(8)
        self.content.addWidget(label("A toolbox for building constructed languages.", None, self))
        self.content.addSpacing(16)

        buttons = QHBoxLayout()
        github = Button("View on GitHub", "external-link", parent=self)
        github.clicked.connect(self.accept)
        buttons.addWidget(github)
        buttons.addStretch()
        close = Button("Close", variant="primary", parent=self)
        close.clicked.connect(self.reject)
        close.setDefault(True)
        buttons.addWidget(close)
        self.content.addLayout(buttons)

    def accept(self):
        from webbrowser import open as web_open
        web_open(GITHUB_URL)

__all__ = ["About"]

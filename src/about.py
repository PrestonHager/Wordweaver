# about.py

from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout, QMainWindow
from pathlib import Path

with open(Path(__file__).parent.joinpath(Path("VERSION")), "r") as f:
    VERSION = f.read().strip()
GITHUB_URL = "https://github.com/PrestonHager/Wordweaver"


class About(QDialog):
    def __init__(self, parent: QMainWindow):
        super().__init__(parent)

        self.setWindowTitle("About")

        self.layout = QVBoxLayout()
        self.label = QLabel(f"Wordweaver is a complete toolbox for all conlanging. \
\n\nVersion: {VERSION}\n\n{GITHUB_URL}")
        self.layout.addWidget(self.label)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Open | QDialogButtonBox.StandardButton.Close)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layout.addWidget(self.buttonBox)

        self.setLayout(self.layout)
        self.buttonBox.button(QDialogButtonBox.StandardButton.Close).setDefault(True)

    def accept(self):
        from webbrowser import open as web_open
        web_open(GITHUB_URL)


__all__ = ["About"]

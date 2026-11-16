# sense_picker.py

from PyQt6.QtCore import QEventLoop, QThread, Qt, pyqtSignal
from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                             QMessageBox, QProgressDialog, QPushButton, QVBoxLayout, QWidget)

from senses import Sense, SenseLookup

class _DownloadThread(QThread):
    # Downloading and unpacking a wordnet takes a minute or two, so it runs here instead of freezing the window.
    failed = pyqtSignal(str)  # pyright: ignore[reportCallIssue]  PyQt6 stub bug, see pyproject.

    def __init__(self, lookup: SenseLookup, parent: QWidget | None=None):
        super().__init__(parent)
        self.lookup = lookup

    def run(self):
        try:
            self.lookup.download()
        except Exception as e:
            self.failed.emit(str(e) or e.__class__.__name__)

def ensure_downloaded(lookup: SenseLookup, parent: QWidget) -> bool:
    """Make sure a dictionary's data is on this computer, asking before downloading it.

    Returns whether the data is ready to search.
    """
    try:
        if lookup.is_downloaded():
            return True
    except Exception as e:
        QMessageBox.warning(parent, "Couldn't Open Dictionary", f"{lookup.name} couldn't be opened.\n\n{e}")
        return False
    # A lookup can say how big its download is. Otherwise we assume it's a wordnet.
    note = getattr(lookup, "download_note", "It needs an internet connection and takes a minute or two, and it only happens once. "
                                            "It uses about 100 MB of disk space.")
    answer = QMessageBox.question(parent, "Download Dictionary", f"{lookup.name} isn't downloaded yet.\n\n{note}\n\nDownload it now?")
    if answer != QMessageBox.StandardButton.Yes:
        return False
    # First, show a busy dialog, since the download can't tell us how far along it is.
    progress = QProgressDialog(f"Downloading {lookup.name}…", None, 0, 0, parent)
    progress.setWindowTitle("Download Dictionary")
    progress.setWindowModality(Qt.WindowModality.WindowModal)
    progress.setMinimumDuration(0)
    errors = []
    thread = _DownloadThread(lookup, parent)
    thread.failed.connect(errors.append)
    # Then run the download, keeping the window responsive until the thread says it's done.
    # The finished signal is queued for this thread, so it can't arrive before the loop starts.
    loop = QEventLoop()
    thread.finished.connect(loop.quit)
    progress.show()
    thread.start()
    loop.exec()
    thread.wait()
    progress.close()
    if errors:
        QMessageBox.warning(parent, "Couldn't Download Dictionary", f"{lookup.name} couldn't be downloaded.\n\n{errors[0]}")
        return False
    return True

class SensePicker(QDialog):
    """Search a dictionary's senses by a Gloss and pick one to link as a Concept Reference."""

    def __init__(self, lookup: SenseLookup, text: str="", parent: QWidget | None=None):
        super().__init__(parent)
        self.lookup = lookup
        self.sense: Sense | None = None
        self._senses: list[Sense] = []
        self.setWindowTitle(f"Link a Sense from {lookup.name}")
        self.resize(520, 360)

        layout = QVBoxLayout(self)
        search_bar = QHBoxLayout()
        self.search_input = QLineEdit(text, self)
        self.search_input.setPlaceholderText("A Gloss, like bank")
        self.search_input.returnPressed.connect(self.search)
        search_bar.addWidget(self.search_input)
        search_button = QPushButton("Search", self)
        search_button.setAutoDefault(False)
        search_button.clicked.connect(self.search)
        search_bar.addWidget(search_button)
        layout.addLayout(search_bar)
        self.status = QLabel("Search for a Gloss to see its senses.", self)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.results = QListWidget(self)
        self.results.setWordWrap(True)
        self.results.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self.results)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel, self)
        self.link_button = QPushButton("Link Sense", self)
        self.link_button.setAutoDefault(False)
        buttons.addButton(self.link_button, QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def search(self):
        text = self.search_input.text().strip()
        if not text:
            return
        # The data only loads now, on the first search, and only downloads if you agree to it.
        if not ensure_downloaded(self.lookup, self):
            self.status.setText(f"{self.lookup.name} isn't downloaded, so there's nothing to search yet.")
            return
        try:
            senses = self.lookup.search(text)
        except Exception as e:
            QMessageBox.warning(self, "Couldn't Search", f"{self.lookup.name} couldn't be searched.\n\n{e}")
            return
        self.show_senses(senses, text)

    def show_senses(self, senses: list[Sense], text: str=""):
        self._senses = senses
        self.results.clear()
        for sense in senses:
            item = QListWidgetItem(sense.label(), self.results)
            item.setToolTip(str(sense.reference))
        if senses:
            self.status.setText(f"{len(senses)} sense{'s' if len(senses) != 1 else ''} of \"{text}\". Pick the one you mean.")
            self.results.setCurrentRow(0)
        else:
            self.status.setText(f"No senses found for \"{text}\".")

    def accept(self):
        row = self.results.currentRow()
        if not 0 <= row < len(self._senses):
            return
        self.sense = self._senses[row]
        super().accept()

__all__ = ["SensePicker", "ensure_downloaded"]

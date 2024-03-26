# main.py

from PyQt6.QtWidgets import QApplication, QFileDialog, QPushButton, QGridLayout, QHBoxLayout, QInputDialog, QLabel, QMainWindow, QMenu, QScrollArea, QSizePolicy, QTextEdit, QVBoxLayout, QWidget
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

from phonology_defaults import DEFAULT_PULMONIC_PHONOLOGY_INVENTORY, DEFAULT_VOWEL_PHONOLOGY_INVENTORY
from wordweaver_project import WordweaverProject

class App(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set class defaults
        self.project = None

        # Construct GUI
        self.setWindowTitle("Wordweaver")

        self.setGeometry(100, 100, 640, 480)

        widget = QWidget(self)
        self.setCentralWidget(widget)
        self.layout = QVBoxLayout(widget)

        # Add text and header
        header = QLabel("Wordweaver", self)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFont(QFont("Arial", 32, QFont.Weight.Bold))
        header.setContentsMargins(0, 0, 0, 20)
        header.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.layout.addWidget(header)
        text = QLabel("Your complete toolbox for all things conglang.\nStart by creating a new project or opening an existing one.", self)
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text.setContentsMargins(20, 0, 0, 20)
        text.setWordWrap(True)
        self.layout.addWidget(text)

        # Add menu buttons
        menubar = self.menuBar()

        file_menu = QMenu("&File", self)
        new_action = file_menu.addAction("&New Project")
        new_action.triggered.connect(self.new_project)
        new_action.setShortcut("Ctrl+N")
        open_action = file_menu.addAction("&Open Project")
        open_action.triggered.connect(self.open_project)
        open_action.setShortcut("Ctrl+O")
        save_action = file_menu.addAction("&Save Project")
        save_action.triggered.connect(self.save)
        save_action.setShortcut("Ctrl+S")
        save_as_action = file_menu.addAction("S&ave Project As")
        save_as_action.triggered.connect(self.save_as)
        save_as_action.setShortcut("Ctrl+Shift+S")
        menubar.addMenu(file_menu)

        edit_menu = QMenu("&Edit", self)
        copy_action = edit_menu.addAction("&Copy")
        copy_action.triggered.connect(self.copy)
        copy_action.setShortcut("Ctrl+C")
        paste_action = edit_menu.addAction("&Paste")
        paste_action.triggered.connect(self.paste)
        paste_action.setShortcut("Ctrl+V")
        # TODO: implement undo and redo
        # edit_menu.addSeparator()
        # undo_action = edit_menu.addAction("&Undo")
        # undo_action.triggered.connect(self.undo)
        # undo_action.setShortcut("Ctrl+Z")
        # redo_action = edit_menu.addAction("&Redo")
        # redo_action.triggered.connect(self.redo)
        # redo_action.setShortcut("Ctrl+Y")
        menubar.addMenu(edit_menu)
    
    def new_project(self):
        # Prompt the user for a project name
        name, ok = QInputDialog.getText(self,
                                        "New Project",
                                        "Enter a name for the new project:",
                                        text="Untitled Project")
        if ok and name:
            self.project = WordweaverProject(name, None, DEFAULT_PULMONIC_PHONOLOGY_INVENTORY, [], DEFAULT_VOWEL_PHONOLOGY_INVENTORY, [])
    
    def open_project(self):
        # If there is an unsaved project, then prompt the user to save it
        if self.project is not None:
            if not self.prompt_save():
                return
        # Ask for a file and load it
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilters(("Wordweaver Project (*.wwproj)", "All Files (*)"))
        if dialog.exec() == QFileDialog.DialogCode.Accepted:
            self.project = WordweaverProject.from_file(dialog.selectedFiles()[0])

    def prompt_save(self) -> bool:
        return True

    def save(self):
        # See if the project has a file associated with it
        if self.project is not None:
            if self.project.file is not None:
                self.project.save()
            else:
                # if it doesn't, use the save as dialog.
                self.save_as()

    def save_as(self):
        # Ask the user for a file name to save the project to
        dialog = QFileDialog(self)
        dialog.selectFile(f"{self.project.name}.wwproj" if self.project is not None else "Untitled Project.wwproj")
        dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        dialog.setDefaultSuffix("wwproj")
        dialog.setNameFilters(("Wordweaver Project (*.wwproj)", "All Files (*)"))
        if dialog.exec() == QFileDialog.DialogCode.Accepted:
            self.project.file = dialog.selectedFiles()[0]
            self.project.save()

    def copy(self):
        pass

    def paste(self):
        pass

    def undo(self):
        pass

    def redo(self):
        pass

if __name__ == "__main__":
    from sys import argv
    app = QApplication(argv)
    window = App()
    window.show()
    app.exec()

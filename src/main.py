# main.py

from PyQt6.QtWidgets import QApplication, QFileDialog, QPushButton, QGridLayout, QHBoxLayout, QInputDialog, QLabel, QMainWindow, QMenu, QScrollArea, QSizePolicy, QTextEdit, QVBoxLayout, QWidget
from PyQt6.QtGui import QCloseEvent, QFont, QIcon
from PyQt6.QtCore import Qt
from os import path
from platformdirs import user_cache_dir
# Note: you may also need user_data_dir,
# user_log_dir, and user_runtime_dir (aka temp folder)

from phonology_defaults import DEFAULT_PULMONIC_PHONOLOGY_INVENTORY, DEFAULT_VOWEL_PHONOLOGY_INVENTORY
from wordweaver_project import WordweaverProject
from phonology_selector import PhonologySelector

class App(QMainWindow):
    def __init__(self, project: WordweaverProject=None):
        super().__init__()

        # Set class defaults
        self.project = project

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

        # Add a welcome message if no project is open
        self.welcome_text = QLabel("Your complete toolbox for all things conglang.\nStart by creating a new project or opening an existing one.", self)
        self.welcome_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcome_text.setContentsMargins(20, 0, 0, 20)
        self.welcome_text.setWordWrap(True)
        if self.project is not None:
            self.welcome_text.hide()
        self.layout.addWidget(self.welcome_text)

        # Create the project view if there is a project
        self.project_view = QWidget(self)
        self.project_view_layout = QGridLayout(self.project_view)

        self.project_name = QLabel("Untitled Project", self.project_view)
        self.project_name.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        self.project_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.project_name.setContentsMargins(0, 0, 0, 20)
        self.project_name.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.project_view_layout.addWidget(self.project_name, 0, 0, 1, 2)

        phonology_label = QLabel("Phonology", self.project_view)
        self.phonology_text = QTextEdit(self.project_view)
        self.phonology_text.setReadOnly(True)
        phonology_edit_button = QPushButton("Edit Phonology", self.project_view)
        phonology_edit_button.clicked.connect(self.edit_phonology)
        self.project_view_layout.addWidget(phonology_label, 1, 0)
        self.project_view_layout.addWidget(self.phonology_text, 2, 0)
        self.project_view_layout.addWidget(phonology_edit_button, 3, 0)

        lexicon_label = QLabel("Lexicon", self.project_view)
        self.lexicon_text = QTextEdit(self.project_view)
        self.lexicon_text.setReadOnly(True)
        lexicon_edit_button = QPushButton("Edit Lexicon", self.project_view)
        lexicon_edit_button.clicked.connect(self.edit_lexicon)
        self.project_view_layout.addWidget(lexicon_label, 1, 1)
        self.project_view_layout.addWidget(self.lexicon_text, 2, 1)
        self.project_view_layout.addWidget(lexicon_edit_button, 3, 1)

        self._update_project_view()

        if self.project is None:
            self.project_view.hide()
        self.layout.addWidget(self.project_view)

        # Add menu buttons
        menubar = self.menuBar()

        file_menu = QMenu("&File", self)
        new_action = file_menu.addAction("&New Project")
        new_action.triggered.connect(self.new_project)
        new_action.setShortcut("Ctrl+N")
        open_action = file_menu.addAction("&Open Project")
        open_action.triggered.connect(self.open_project)
        open_action.setShortcut("Ctrl+O")
        close_action = file_menu.addAction("&Close Project")
        close_action.triggered.connect(self.close_project)
        close_action.setShortcut("Ctrl+W")
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

    def _update_main_view(self):
        if self.project is None:
            self.welcome_text.show()
            self.project_view.hide()
        else:
            self.welcome_text.hide()
            self.project_view.show()
            self._update_project_view()

    def _update_project_view(self):
        if self.project is not None:
            self.project_name.setText(self.project.name)
            phonology_text = "C = " + ', '.join(map(str, self.project.pulmonic_inventory)) if len(self.project.pulmonic_inventory) > 0 else ""
            phonology_text += "\nB = " + ', '.join(map(str, self.project.non_pulmonic_inventory)) if len(self.project.non_pulmonic_inventory) > 0 else ""
            phonology_text += "\nV = " + ', '.join(map(str, self.project.vowel_inventory)) if len(self.project.vowel_inventory) > 0 else ""
            self.phonology_text.setText(phonology_text)
            self.lexicon_text.setText(', '.join(self.project.lexicon))

    def new_project(self):
        # Prompt the user for a project name
        name, ok = QInputDialog.getText(self,
                                        "New Project",
                                        "Enter a name for the new project:",
                                        text="Untitled Project")
        if ok and name:
            self.project = WordweaverProject(name, None, DEFAULT_PULMONIC_PHONOLOGY_INVENTORY, [], DEFAULT_VOWEL_PHONOLOGY_INVENTORY, [])
            self._update_main_view()
    
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
            self._update_main_view()

    def close_project(self):
        # If there is an unsaved project, then prompt the user to save it
        if self.project is not None:
            if not self.prompt_save():
                return
        self.project = None
        self._update_main_view()

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

    def edit_phonology(self):
        if not hasattr(self, "phonology_selector"):
            self.phonology_selector = PhonologySelector(self.project)
        self.phonology_selector.show()
        self.phonology_selector.activateWindow()
        self.phonology_selector.closeEvent = self._close_phonology_selector

    def edit_lexicon(self):
        pass

    def _close_phonology_selector(self, a0: QCloseEvent | None) -> None:
        self.project = self.phonology_selector.project
        self._update_project_view()
        return super().closeEvent(a0)

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        # If there is an unsaved project, then prompt the user to save it
        if self.project is not None:
            if not self.prompt_save():
                pass
            # Save the window metadata for later
            with open(path.join(user_cache_dir("Wordweaver", False, ensure_exists=True), ".editor"), "w") as f_out:
                f_out.write(f"{self.project.file}")
        return super().closeEvent(a0)

if __name__ == "__main__":
    import sys
    basedir = path.dirname(__file__)
    # Set the application ID for Windows
    try:
        from ctypes import windll
        myappid = 'xyz.prestonhager.wordweaver'
        windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except ImportError:
        pass
    # Look for current cache file
    if path.exists(path.join(user_cache_dir("Wordweaver", False, ensure_exists=True), ".editor")):
        with open(path.join(user_cache_dir("Wordweaver", False), ".editor"), "r") as f_in:
            project_file = f_in.read().strip()
        if path.exists(project_file):
            project = WordweaverProject.from_file(project_file)
        else:
            project = None
    # Create an application and run it
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(path.join(basedir, "wordweaver.ico")))
    window = App(project)
    window.show()
    app.exec()

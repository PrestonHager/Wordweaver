# main.py

from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QPushButton, QGridLayout, QInputDialog, QLabel,
    QMainWindow, QMenu, QSizePolicy, QTextEdit, QVBoxLayout, QWidget
)
from PyQt6.QtGui import QCloseEvent, QFont, QIcon
from PyQt6.QtCore import Qt
from pathlib import Path
from platformdirs import user_cache_path, user_log_path
# Note: you may also need user_data_dir,
# user_log_dir, and user_runtime_dir (aka temp folder)

import logging
import pyperclip

from about import About
from wordweaver_project import WordweaverProject
from phonology_selector import PhonologySelector

WELCOME_TEXT = """Your complete toolbox for all things conglang.
Start by creating a new project or opening an existing one."""


class App(QMainWindow):
    def __init__(self, project: WordweaverProject = None):
        super().__init__()

        # Setup the logger
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)

        # Set class defaults
        self.project = project

        # Construct GUI
        self.logger.debug("Constructing GUI")
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
        self.welcome_text = QLabel(WELCOME_TEXT, self)
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
        self.logger.debug("Creating menubar and actions")
        menubar = self.menuBar()

        self.file_menu = QMenu("&File", self)
        new_action = self.file_menu.addAction("&New Project")
        new_action.triggered.connect(self.new_project)
        new_action.setShortcut("Ctrl+N")
        open_action = self.file_menu.addAction("&Open Project")
        open_action.triggered.connect(self.open_project)
        open_action.setShortcut("Ctrl+O")
        close_action = self.file_menu.addAction("&Close Project")
        close_action.triggered.connect(self.close_project)
        close_action.setShortcut("Ctrl+W")
        close_action.setEnabled(self.project is not None)
        self.file_menu.addSeparator()
        save_action = self.file_menu.addAction("&Save Project")
        save_action.triggered.connect(self.save)
        save_action.setShortcut("Ctrl+S")
        save_action.setEnabled(self.project is not None)
        save_as_action = self.file_menu.addAction("S&ave Project As")
        save_as_action.triggered.connect(self.save_as)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.setEnabled(self.project is not None)
        self.file_menu.addSeparator()
        about_action = self.file_menu.addAction("A&bout")
        about_action.triggered.connect(self.open_about)
        about_action.setShortcut("F1")
        exit_action = self.file_menu.addAction("&Exit")
        exit_action.triggered.connect(self.close)
        exit_action.setShortcut("Alt+F4")
        menubar.addMenu(self.file_menu)

        self.edit_menu = QMenu("&Edit", self)
        copy_action = self.edit_menu.addAction("&Copy")
        copy_action.triggered.connect(self.copy)
        copy_action.setShortcut("Ctrl+C")
        copy_action.setEnabled(self.project is not None)
        paste_action = self.edit_menu.addAction("&Paste")
        paste_action.triggered.connect(self.paste)
        paste_action.setShortcut("Ctrl+V")
        paste_action.setEnabled(self.project is not None and pyperclip.paste() != '')
        # TODO: implement undo and redo
        # self.edit_menu.addSeparator()
        # undo_action = self.edit_menu.addAction("&Undo")
        # undo_action.triggered.connect(self.undo)
        # undo_action.setShortcut("Ctrl+Z")
        # redo_action = self.edit_menu.addAction("&Redo")
        # redo_action.triggered.connect(self.redo)
        # redo_action.setShortcut("Ctrl+Y")
        menubar.addMenu(self.edit_menu)

    def _update_main_view(self):
        # Set menu action states
        # Close project
        self.file_menu.actions()[2].setEnabled(self.project is not None)
        # Save project and save as
        self.file_menu.actions()[4].setEnabled(self.project is not None)
        self.file_menu.actions()[5].setEnabled(self.project is not None)
        # Copy and paste
        self.edit_menu.actions()[0].setEnabled(self.project is not None)
        self.edit_menu.actions()[1].setEnabled(self.project is not None and pyperclip.paste() != '')
        # Set project view and welcome message visibility
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
            phonology_text = ""
            if len(self.project.pulmonic_inventory) > 0:
                phonology_text += "C = " + ', '.join(map(str,
                                                     self.project.pulmonic_inventory))
                phonology_text += "\n"
            if len(self.project.non_pulmonic_inventory) > 0:
                phonology_text += "B = " + ', '.join(map(str,
                                                     self.project.non_pulmonic_inventory))
                phonology_text += "\n"
            if len(self.project.vowel_inventory) > 0:
                phonology_text += "V = " + ', '.join(map(str,
                                                     self.project.vowel_inventory))
            self.phonology_text.setText(phonology_text)
            self.lexicon_text.setText(', '.join(self.project.lexicon))

    def new_project(self):
        # Prompt the user for a project name
        name, ok = QInputDialog.getText(self,
                                        "New Project",
                                        "Enter a name for the new project:",
                                        text="Untitled Project")
        if ok and name:
            try:
                self.project = WordweaverProject.from_file(Path(__file__).parent.joinpath(Path("default.wwproj").absolute()))
            except FileNotFoundError:
                self.logger.warning("Default project file not found; creating new empty project.")
                self.project = WordweaverProject(name)
            self.project.name = name
            self.project.file = None
            self._update_main_view()
            self.logger.info(f"Created new project: {name}")

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
            self.logger.info(f"Opened project: {self.project.name}")

    def close_project(self):
        # If there is an unsaved project, then prompt the user to save it
        if self.project is not None:
            if not self.prompt_save():
                return
        self.project = None
        self._update_main_view()
        self.logger.info("Closed current project")

    def prompt_save(self) -> bool:
        return True

    def save(self):
        # See if the project has a file associated with it
        if self.project is not None:
            if self.project.file is not None:
                self.project.save()
                self.logger.info(f"Saved project \"{self.project.name}\" to {self.project.file}")
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
            self.logger.info(f"Saved project \"{self.project.name}\" to \
{self.project.file} and updated project file location.")

    def open_about(self):
        if not hasattr(self, "about_window"):
            self.about_window = About(self)
            self.logger.debug("Created about window")
        self.about_window.show()
        self.about_window.activateWindow()
        self.about_window.closeEvent = self._close_about_window

    def copy(self):
        # Copy the current phonology text
        pyperclip.copy(self.phonology_text.toPlainText())

    def paste(self):
        # Use the following command to paste
        pyperclip.paste()

    def undo(self):
        pass

    def redo(self):
        pass

    def edit_phonology(self):
        if not hasattr(self, "phonology_selector"):
            self.phonology_selector = PhonologySelector(self.project)
            self.logger.debug("Created new phonology selector window")
        self.phonology_selector.show()
        self.phonology_selector.activateWindow()
        self.phonology_selector.closeEvent = self._close_phonology_selector

    def edit_lexicon(self):
        pass

    def _close_about_window(self, a0: QCloseEvent | None) -> None:
        delattr(self, "about_window")
        return super().closeEvent(a0)

    def _close_phonology_selector(self, a0: QCloseEvent | None) -> None:
        self.project = self.phonology_selector.project
        self._update_project_view()
        self.logger.debug("Closed phonology selector window and updated project")
        self.logger.info(f"Updated phonology to {self.project.inventory}")
        delattr(self, "phonology_selector")
        return super().closeEvent(a0)

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        # If there is an unsaved project, then prompt the user to save it
        if self.project is not None:
            if not self.prompt_save():
                pass
            # Save the window metadata for later
            with open(user_cache_path("Wordweaver", False, ensure_exists=True).joinpath(Path(".editor")), "w") as f_out:
                f_out.write(f"{self.project.file}")
            self.logger.info("Saved project file location to cache file.")
        else:
            # Remove the cache file if there is no project
            if user_cache_path("Wordweaver", False).joinpath(Path(".editor")).exists():
                self.logger.info("Removing cache file.")
                user_cache_path("Wordweaver", False).joinpath(Path(".editor")).unlink()
        return super().closeEvent(a0)


if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Wordweaver: A complete toolbox for all things conlang.")
    parser.add_argument("-v", "--verbose",
                        action="store",
                        help="Enable verbose logging",
                        default="WARNING",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    args = parser.parse_args()
    # Setup logging defaults
    logging.basicConfig(filename=user_log_path("Wordweaver", False, ensure_exists=True).joinpath(Path("wordweaver.log")),
                        encoding="utf-8",
                        level=args.verbose,
                        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    import sys
    logger = logging.getLogger(__name__)
    basedir = Path(__file__).parent
    # Set the application ID for Windows
    try:
        from ctypes import windll
        logger.debug("Setting application ID for Windows")
        myappid = 'com.prestonhager.wordweaver'
        windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except ImportError:
        pass
    # Look for current cache file
    if user_cache_path("Wordweaver", False).joinpath(Path(".editor")).exists():
        logger.info("Found cache file, trying to load project...")
        with open(user_cache_path("Wordweaver", False).joinpath(Path(".editor")), "r") as f_in:
            project_file = f_in.read().strip()
        if Path(project_file).exists():
            project = WordweaverProject.from_file(project_file)
            logger.info("Successfully loaded project from cache file.")
        else:
            project = None
            logger.info("Failed to load project from cache file.")
    else:
        project = None
    # Create an application and run it
    logger.debug("Create application")
    app = QApplication(sys.argv)
    icon = QIcon()
    icon.addFile(str(basedir.joinpath(Path("icons/wordweaver.ico")).absolute()))
    app.setWindowIcon(icon)
    window = App(project)
    window.show()
    logger.debug("Running application")
    app.exec()

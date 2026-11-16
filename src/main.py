# main.py

from PyQt6.QtWidgets import QApplication, QButtonGroup, QComboBox, QFileDialog, QHBoxLayout, QInputDialog, QMainWindow, QMenu, QMessageBox, QStackedWidget, QVBoxLayout, QWidget
from PyQt6.QtGui import QCloseEvent, QIcon
from PyQt6.QtCore import Qt
from pathlib import Path
from platformdirs import user_cache_path, user_log_path
# Note: you may also need user_data_dir,
# user_log_dir, and user_runtime_dir (aka temp folder)

import logging
import pyperclip

from about import About
from icons import bind_icon, icon as make_icon
from lexicon_page import LexiconPage
from pages import OverviewPage, WelcomePage
from phonology_page import PhonologyPage
from theme import theme
from widgets import Button, label
from wordweaver_project import Language, LanguageKind, Project, ProjectFileError

# The sidebar pages, in order: key, label, and Lucide icon.
NAV = [
    ("overview", "Overview", "layout-dashboard"),
    ("phonology", "Phonology", "audio-lines"),
    ("lexicon", "Lexicon", "book-open"),
]

class App(QMainWindow):
    def __init__(self, project: Project=None):
        super().__init__()

        # Setup the logger
        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)

        # Set class defaults
        self.project = project
        # The Language being edited, picked from the sidebar.
        self.language: Language | None = None

        # Construct GUI
        self.logger.debug("Constructing GUI")
        self.setWindowTitle("Wordweaver")
        self.resize(1240, 800)
        self.setMinimumSize(900, 600)

        # The window holds two things: the welcome page with no Project, and the workspace with one.
        self.root = QStackedWidget(self)
        self.setCentralWidget(self.root)
        self.welcome = WelcomePage(self.root)
        self.welcome.new_requested.connect(self.new_project)
        self.welcome.open_requested.connect(self.open_project)
        self.root.addWidget(self.welcome)

        self.workspace = QWidget(self.root)
        workspace_layout = QHBoxLayout(self.workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(0)
        workspace_layout.addWidget(self._build_sidebar(self.workspace))
        self.pages = QStackedWidget(self.workspace)
        workspace_layout.addWidget(self.pages, 1)
        self.root.addWidget(self.workspace)

        # Now the pages the sidebar switches between.
        self.overview_page = OverviewPage(self.pages)
        self.overview_page.add_requested.connect(self.add_language)
        self.overview_page.rename_project_requested.connect(self.rename_project)
        self.overview_page.phonology_requested.connect(lambda language: self._open_page("phonology", language))
        self.overview_page.rename_requested.connect(self.rename_language)
        self.overview_page.remove_requested.connect(self.remove_language)
        self.overview_page.kind_changed.connect(self._on_kind_changed)
        self.phonology_page = PhonologyPage(self.pages)
        self.phonology_page.changed.connect(self._on_inventory_changed)
        self.lexicon_page = LexiconPage(self.pages)
        self.page_widgets = {"overview": self.overview_page, "phonology": self.phonology_page, "lexicon": self.lexicon_page}
        for page in self.page_widgets.values():
            self.pages.addWidget(page)

        self._build_menus()
        self.statusBar().setSizeGripEnabled(False)
        self._open_page("overview")
        self._update_main_view()

    def _build_sidebar(self, parent: QWidget) -> QWidget:
        sidebar = QWidget(parent)
        sidebar.setObjectName("Sidebar")
        sidebar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        sidebar.setFixedWidth(232)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(14, 18, 14, 14)
        layout.setSpacing(4)

        # First, the app and Project names at the top.
        app_name = label("Wordweaver", None, sidebar)
        app_name.setObjectName("AppName")
        layout.addWidget(app_name)
        self.sidebar_project = label("", "muted", sidebar)
        layout.addWidget(self.sidebar_project)
        layout.addSpacing(18)

        # Then the Language picker, with a button to add another.
        layout.addWidget(label("LANGUAGE", "section", sidebar))
        picker_row = QHBoxLayout()
        picker_row.setSpacing(6)
        self.language_picker = QComboBox(sidebar)
        self.language_picker.currentIndexChanged.connect(self._on_language_picked)
        picker_row.addWidget(self.language_picker, 1)
        add = Button(icon="plus", variant="ghost", tooltip="Add Language", parent=sidebar)
        add.clicked.connect(self.add_language)
        picker_row.addWidget(add)
        layout.addLayout(picker_row)
        layout.addSpacing(18)

        # Now the page buttons, only one of which is checked at a time.
        self.nav = QButtonGroup(sidebar)
        self.nav.setExclusive(True)
        self.nav_buttons = {}
        for key, text, icon_name in NAV:
            button = Button(text, icon_name, "nav", parent=sidebar)
            button.setCheckable(True)
            button.clicked.connect(lambda _checked, k=key: self._open_page(k))
            self.nav.addButton(button)
            self.nav_buttons[key] = button
            layout.addWidget(button)
        layout.addStretch()

        # Finally, the theme toggle and About at the bottom.
        bottom = QHBoxLayout()
        self.theme_button = Button(variant="ghost", parent=sidebar)
        self.theme_button.setFixedSize(32, 32)
        self.theme_button.clicked.connect(self.toggle_theme)
        bottom.addWidget(self.theme_button)
        about = Button(icon="info", variant="ghost", tooltip="About Wordweaver", parent=sidebar)
        about.clicked.connect(self.open_about)
        bottom.addWidget(about)
        bottom.addStretch()
        layout.addLayout(bottom)
        theme.changed.connect(self._update_theme_button)
        self._update_theme_button()
        return sidebar

    def _build_menus(self):
        self.logger.debug("Creating menubar and actions")
        menubar = self.menuBar()
        self.menu_actions = {}

        # Each entry is the key, label, icon, shortcut, and slot. None makes a separator.
        self.file_menu = QMenu("&File", self)
        for entry in (
            ("new", "&New Project", "file-plus", "Ctrl+N", self.new_project),
            ("open", "&Open Project", "folder-open", "Ctrl+O", self.open_project),
            ("close", "&Close Project", "x", "Ctrl+W", self.close_project),
            None,
            ("save", "&Save Project", "save", "Ctrl+S", self.save),
            ("save_as", "S&ave Project As", "save-all", "Ctrl+Shift+S", self.save_as),
            ("export_csv", "&Export Lexicon to CSV…", None, "", self.export_lexicon_csv),
            None,
            ("about", "A&bout", "info", "F1", self.open_about),
            ("exit", "&Exit", "log-out", "Alt+F4", self.close),
        ):
            if entry is None:
                self.file_menu.addSeparator()
            else:
                self.menu_actions[entry[0]] = self._action(self.file_menu, *entry[1:])
        menubar.addMenu(self.file_menu)

        self.edit_menu = QMenu("&Edit", self)
        self.menu_actions["copy"] = self._action(self.edit_menu, "&Copy Phoneme Inventory", "copy", "Ctrl+Shift+C", self.copy)
        self.menu_actions["paste"] = self._action(self.edit_menu, "&Paste", "clipboard-paste", "Ctrl+V", self.paste)
        # TODO: implement undo and redo
        menubar.addMenu(self.edit_menu)

        self.view_menu = QMenu("&View", self)
        for number, (key, text, icon_name) in enumerate(NAV, start=1):
            self.menu_actions[key] = self._action(self.view_menu, f"&{text}", icon_name, f"Ctrl+{number}", lambda _=False, k=key: self._open_page(k))
        self.view_menu.addSeparator()
        self.menu_actions["theme"] = self._action(self.view_menu, "Toggle &Dark Mode", "moon", "Ctrl+Shift+L", self.toggle_theme)
        menubar.addMenu(self.view_menu)

    def _action(self, menu: QMenu, text: str, icon_name: str | None, shortcut: str, slot):
        action = menu.addAction(text)
        if icon_name is not None:
            bind_icon(action, icon_name, "muted", size=16)
        action.setShortcut(shortcut)
        action.triggered.connect(slot)
        return action

    def _update_main_view(self):
        # First, turn the menu actions on or off for whether a Project is open.
        has_project = self.project is not None
        for key in ("close", "save", "save_as", "export_csv", "copy", "overview", "phonology", "lexicon"):
            self.menu_actions[key].setEnabled(has_project)
        self.menu_actions["paste"].setEnabled(has_project and pyperclip.paste() != '')
        # Then show the welcome page or the workspace.
        if not has_project:
            self.language = None
            self.root.setCurrentWidget(self.welcome)
            self.setWindowTitle("Wordweaver")
            return
        self.root.setCurrentWidget(self.workspace)
        self._update_project_view()

    def _update_project_view(self):
        if self.project is None:
            self.language = None
            return
        self.setWindowTitle(f"{self.project.name} - Wordweaver")
        self.sidebar_project.setText(self.project.name)
        # First, make sure there's a Language to edit, and that the picked one is still in the Project.
        if not self.project.languages:
            self.project.add_language(self.project.name)
        if self.language not in self.project.languages:
            self.language = self.project.languages[0]
        # Now refill the picker without its signal firing halfway through.
        self.language_picker.blockSignals(True)
        self.language_picker.clear()
        for language in self.project.languages:
            self.language_picker.addItem(language.name, language.id)
        self.language_picker.setCurrentIndex(self.project.languages.index(self.language))
        self.language_picker.blockSignals(False)
        # Finally, refresh the pages for the picked Language.
        self.overview_page.refresh(self.project, self.language)
        self.phonology_page.set_language(self.language)
        self.lexicon_page.refresh(self.project, self.language)

    def _open_page(self, key: str, language: Language | None = None):
        # Switch Language first if a card asked for a different one.
        if language is not None and language is not self.language:
            self.language = language
            self._update_project_view()
        self.pages.setCurrentWidget(self.page_widgets[key])
        self.nav_buttons[key].setChecked(True)

    def _on_language_picked(self, index: int):
        if self.project is None or index < 0:
            return
        self.language = self.project.languages[index]
        self._update_project_view()

    def _on_kind_changed(self, language: Language, kind: LanguageKind):
        language.kind = kind

    def _on_inventory_changed(self):
        # The Overview cards show the inventory, so keep them current.
        self.overview_page.refresh(self.project, self.language)

    def _update_theme_button(self):
        # Show the mode you'd switch to, like most apps do.
        dark = theme.is_dark
        self.theme_button.setIcon(make_icon("sun" if dark else "moon"))
        self.theme_button.setToolTip("Switch to light mode" if dark else "Switch to dark mode")

    def toggle_theme(self):
        theme.toggle(QApplication.instance())

    def add_language(self):
        if self.project is None:
            return
        name, ok = QInputDialog.getText(self, "Add Language", "Enter a name for the new Language:")
        if ok and name:
            self.language = self.project.add_language(name)
            self._update_project_view()
            self.logger.info(f"Added Language: {name}")

    def rename_language(self, language: Language | None = None):
        language = language or self.language
        name, ok = QInputDialog.getText(self, "Rename Language", "Enter a new name for the Language:", text=language.name)
        if ok and name:
            language.name = name
            self._update_project_view()

    def remove_language(self, language: Language | None = None):
        language = language or self.language
        if len(self.project.languages) == 1:
            QMessageBox.information(self, "Can't Remove Language", "A Project needs at least one Language.")
            return
        answer = QMessageBox.question(self, "Remove Language", f"Remove {language.name} and everything in it?")
        if answer == QMessageBox.StandardButton.Yes:
            self.project.remove_language(language)
            self.logger.info(f"Removed Language: {language.name}")
            if language is self.language:
                self.language = None
            self._update_project_view()

    def rename_project(self):
        name, ok = QInputDialog.getText(self, "Rename Project", "Enter a new name for the Project:", text=self.project.name)
        if ok and name:
            self.project.name = name
            self._update_project_view()

    def new_project(self):
        # Prompt the user for a project name
        name, ok = QInputDialog.getText(self,
                                        "New Project",
                                        "Enter a name for the new project:",
                                        text="Untitled Project")
        if ok and name:
            try:
                self.project = Project.load(Path(__file__).parent.joinpath(Path("default.wwproj")).absolute())
            except (FileNotFoundError, ProjectFileError) as e:
                self.logger.warning(f"Couldn't load the default project ({e}); creating new empty project.")
                self.project = Project(name)
            self.project.name = name
            self.project.file = None
            self._open_page("overview")
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
            try:
                self.project = Project.load(dialog.selectedFiles()[0])
            except (OSError, ProjectFileError) as e:
                self.logger.warning(f"Couldn't open project: {e}")
                QMessageBox.warning(self, "Couldn't Open Project", str(e))
                return
            self.language = None
            self._open_page("overview")
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
                self.statusBar().showMessage(f"Saved to {self.project.file}", 4000)
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
            self.statusBar().showMessage(f"Saved to {self.project.file}", 4000)
            self.logger.info(f"Saved project \"{self.project.name}\" to {self.project.file} and updated project file location.")

    def export_lexicon_csv(self):
        if self.project is None or self.language is None:
            return
        # Ask where to save the current Language's Lexicon.
        dialog = QFileDialog(self)
        dialog.selectFile(f"{self.language.name} Lexicon.csv")
        dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        dialog.setDefaultSuffix("csv")
        dialog.setNameFilters(("CSV File (*.csv)", "All Files (*)"))
        if dialog.exec() != QFileDialog.DialogCode.Accepted:
            return
        file = dialog.selectedFiles()[0]
        # The text already starts with a byte order mark, so plain UTF-8 keeps it, and newline="" keeps the CSV's line endings.
        try:
            with open(file, "w", encoding="utf-8", newline="") as f:
                f.write(self.project.export_lexicon_csv(self.language))
        except OSError as e:
            QMessageBox.warning(self, "Couldn't Export Lexicon", str(e))
            return
        self.statusBar().showMessage(f"Exported the Lexicon to {file}", 4000)
        self.logger.info(f"Exported the Lexicon of \"{self.language.name}\" to {file}")

    def open_about(self):
        if not hasattr(self, "about_window"):
            self.about_window = About(self)
            self.logger.debug("Created about window")
        self.about_window.show()
        self.about_window.activateWindow()
        self.about_window.closeEvent = self._close_about_window

    def copy(self):
        # Copy the current Language's Phoneme Inventory.
        self.phonology_page.copy()
        self.statusBar().showMessage("Copied the Phoneme Inventory", 3000)

    def paste(self):
        # Use the following command to paste
        pyperclip.paste()

    def undo(self):
        pass

    def redo(self):
        pass

    def _close_about_window(self, a0: QCloseEvent | None) -> None:
        delattr(self, "about_window")
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

def main():
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Wordweaver: A complete toolbox for all things conlang.")
    parser.add_argument("-v", "--verbose", action="store", help="Enable verbose logging", default="WARNING", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    args = parser.parse_args()
    # Setup logging defaults
    logging.basicConfig(filename=user_log_path("Wordweaver", False, ensure_exists=True).joinpath(Path("wordweaver.log")), encoding="utf-8", level=args.verbose, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    import sys
    logger = logging.getLogger(__name__)
    basedir = Path(__file__).parent
    # Set the application ID for Windows
    try:
        from ctypes import windll
        logger.debug("Setting application ID for Windows")
        myappid = 'xyz.prestonhager.wordweaver'
        windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except ImportError:
        pass
    # Look for current cache file
    if user_cache_path("Wordweaver", False).joinpath(Path(".editor")).exists():
        logger.info("Found cache file, trying to load project...")
        with open(user_cache_path("Wordweaver", False).joinpath(Path(".editor")), "r") as f_in:
            project_file = f_in.read().strip()
        # Old pre-v1 project files can't be opened anymore, so those fail here too.
        try:
            project = Project.load(project_file)
            logger.info("Successfully loaded project from cache file.")
        except (OSError, ProjectFileError) as e:
            project = None
            logger.info(f"Failed to load project from cache file: {e}")
    else:
        project = None
    # Create an application and run it
    logger.debug("Create application")
    app = QApplication(sys.argv)
    icon = QIcon()
    icon.addFile(str(basedir.joinpath(Path("icons/wordweaver.ico")).absolute()))
    app.setWindowIcon(icon)
    # Apply the theme before building any widgets, so their icons get the right colors.
    theme.apply(app)
    theme.follow_system(app)
    window = App(project)
    window.show()
    logger.debug("Running application")
    app.exec()

if __name__ == "__main__":
    main()

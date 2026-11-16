# phonotactics_page.py

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QAbstractItemView, QCheckBox, QComboBox, QFrame, QHBoxLayout, QLayout, QLineEdit, QListWidget, QListWidgetItem, QScrollArea, QSpinBox, QVBoxLayout, QWidget

from lexicon import Form
from phonotactics import ConstraintAtom, ConstraintMode, Position, SyllablePart, SyllablePosition, SyllableStructure, parse_notation, write_notation, write_syllables
from widgets import Button, Card, FlowLayout, PageHeader, label
from wordweaver_project import Language

class StructureView(QWidget):
    """Draws a Syllable Structure's positions, grouped under Onset, Nucleus, and Coda. Optional positions are dashed."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)  # pyright: ignore[reportArgumentType]  PyQt6 stub bug, see pyproject.
        self.row = QHBoxLayout(self)
        self.row.setContentsMargins(0, 0, 0, 0)
        self.row.setSpacing(18)
        self.parts: dict[SyllablePart, list[str]] = {}

    def _clear_layout(self, layout: QLayout):
        while layout.count():
            item = layout.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)  # pyright: ignore[reportArgumentType]  PyQt6 stub bug, see pyproject.
                widget.deleteLater()
                continue
            child_layout = item.layout()
            if child_layout is not None:
                self._clear_layout(child_layout)
                child_layout.deleteLater()

    def show_positions(self, positions: list[Position]):
        # First, clear out the last structure.
        while self.row.count():
            item = self.row.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    layout = item.layout()
                    if layout is not None:
                        self._clear_layout(layout)
                        layout.deleteLater()
        # Then draw each part that has positions, with its name under it.
        self.parts = {}
        for part in SyllablePart:
            in_part = [p for p in positions if p.part is part]
            if not in_part:
                continue
            self.parts[part] = [f"({p.label})" if p.optional else p.label for p in in_part]
            group = QVBoxLayout()
            group.setSpacing(4)
            boxes = QHBoxLayout()
            boxes.setSpacing(4)
            for position in in_part:
                box = label(position.label, "position", self)
                box.setProperty("optional", position.optional)
                name = position.phoneme_class.name if position.phoneme_class is not None else "no Class"
                box.setToolTip(f"{name}, optional" if position.optional else name)
                boxes.addWidget(box)
            group.addLayout(boxes)
            group.addWidget(label(str(part).upper(), "section", self))
            self.row.addLayout(group)
        self.row.addStretch()

class StructuresCard(Card):
    """Lists a Language's Syllable Structures, with a builder to add and edit them."""

    # Sent whenever a structure changes, so the Form check can run again.
    changed = pyqtSignal()  # pyright: ignore[reportCallIssue]  PyQt6 stub bug, see pyproject.

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.language: Language | None = None
        self.selected: SyllableStructure | None = None

        # First, the title and a short how-to.
        title_row = QHBoxLayout()
        title_row.addWidget(label("SYLLABLE STRUCTURES", "section"))
        self.count = label("0", "badge")
        title_row.addWidget(self.count)
        title_row.addStretch()
        self.content.addLayout(title_row)
        how_to = label("Write each structure like (C)V(C). Each letter is a Phoneme Class label, and parentheses make a position optional. "
                       "Put positions next to each other for a cluster, like (C)(C)V.", "muted", self)
        how_to.setWordWrap(True)
        self.content.addWidget(how_to)

        # Then the list of structures.
        self.list = QListWidget(self)
        self.list.setObjectName("EntryList")
        self.list.setMinimumHeight(80)
        self.list.setMaximumHeight(180)
        self.list.currentItemChanged.connect(self._on_picked)
        self.content.addWidget(self.list)

        # Now the builder: a button for each label, and the notation it writes.
        self.content.addWidget(label("BUILDER", "section", self))
        self.labels_box = QWidget(self)
        self.labels = FlowLayout(self.labels_box)
        self.content.addWidget(self.labels_box)
        notation_row = QHBoxLayout()
        self.optional = QCheckBox("Optional", self)
        self.optional.setToolTip("Add the next position in parentheses")
        notation_row.addWidget(self.optional)
        self.notation_input = QLineEdit(self)
        self.notation_input.setPlaceholderText("Notation, like (C)V(C)")
        self.notation_input.textChanged.connect(self._preview)
        self.notation_input.returnPressed.connect(self.save_structure)
        notation_row.addWidget(self.notation_input, 1)
        self.back_button = Button(icon="x", variant="ghost", tooltip="Take off the last position", parent=self)
        self.back_button.clicked.connect(self.remove_last_position)
        notation_row.addWidget(self.back_button)
        self.content.addLayout(notation_row)
        self.preview = StructureView(self)
        self.content.addWidget(self.preview)

        # Finally, the buttons and a place for errors.
        buttons = QHBoxLayout()
        self.add_button = Button("Add Structure", "plus", "primary", parent=self)
        self.add_button.clicked.connect(self.add_structure)
        buttons.addWidget(self.add_button)
        self.save_button = Button("Save Changes", "save", parent=self)
        self.save_button.clicked.connect(self.save_structure)
        buttons.addWidget(self.save_button)
        self.remove_button = Button("Remove", "trash-2", "danger", parent=self)
        self.remove_button.clicked.connect(self.remove_structure)
        buttons.addWidget(self.remove_button)
        buttons.addStretch()
        self.content.addLayout(buttons)
        self.error = label("", "error", self)
        self.error.setWordWrap(True)
        self.error.hide()
        self.content.addWidget(self.error)

    def set_language(self, language: Language | None):
        self.language = language
        self.selected = None
        self.notation_input.clear()
        self.refresh()

    def refresh(self):
        structures = self.language.phonotactics.syllable_structures if self.language is not None else []
        if self.selected not in structures:
            self.selected = None
        # First, refill the list, noting any structure that can't be used right now.
        self.list.blockSignals(True)
        self.list.clear()
        for structure in structures:
            text = structure.notation
            problem = structure.problem
            if problem is None:
                text += "    " + "  ·  ".join(f"{part}: {''.join(f'({p.label})' if p.optional else p.label for p in structure.part(part))}"
                                              for part in SyllablePart if structure.part(part))
            else:
                text += f"    ⚠ {problem}"
            item = QListWidgetItem(text, self.list)
            item.setData(Qt.ItemDataRole.UserRole, structure.id)
            if structure is self.selected:
                self.list.setCurrentItem(item)
        self.list.blockSignals(False)
        self.count.setText(str(len(structures)))
        # Then a builder button for every labelled Class.
        self.labels.clear()
        classes = [c for c in self.language.classes if c.label] if self.language is not None else []
        for phoneme_class in classes:
            button = Button(phoneme_class.label, parent=self.labels_box)
            symbols = " ".join(phoneme_class.symbols) or "no Phonemes yet"
            button.setToolTip(f"{phoneme_class.name}: {symbols}")
            button.clicked.connect(lambda _checked=False, l=phoneme_class.label: self.add_position(l))
            self.labels.addWidget(button)
        self._show_selected()

    def _on_picked(self, item: QListWidgetItem | None):
        if item is None or self.language is None:
            self.selected = None
        else:
            id = item.data(Qt.ItemDataRole.UserRole)
            self.selected = next((s for s in self.language.phonotactics.syllable_structures if s.id == id), None)
        self._show_error(None)
        self._show_selected()

    def _show_selected(self):
        # Load the picked structure into the builder, so it can be changed and saved.
        self.save_button.setEnabled(self.selected is not None)
        self.remove_button.setEnabled(self.selected is not None)
        self.add_button.setEnabled(self.language is not None)
        if self.selected is not None:
            self.notation_input.setText(self.selected.notation)
        self._preview()

    def _preview(self):
        # Show the parts of whatever's typed, using a throwaway structure so nothing is saved.
        if self.language is None:
            self.preview.show_positions([])
            return
        try:
            parse_notation(self.notation_input.text())
        except ValueError:
            self.preview.show_positions([])
            return
        probe = SyllableStructure(0, self.language.phonotactics, self.notation_input.text())
        self.preview.show_positions(probe.positions)

    def add_position(self, position_label: str):
        # The builder only ever writes notation, so it goes through the same checks as typing it.
        text = self.notation_input.text().strip()
        self.notation_input.setText(text + (f"({position_label})" if self.optional.isChecked() else position_label))

    def remove_last_position(self):
        try:
            positions = parse_notation(self.notation_input.text())
        except ValueError:
            self.notation_input.clear()
            return
        self.notation_input.setText(write_notation(positions[:-1]))

    def add_structure(self):
        if self.language is None:
            return
        try:
            self.selected = self.language.phonotactics.add_syllable_structure(self.notation_input.text())
        except ValueError as e:
            self._show_error(str(e))
            return
        self._done()

    def save_structure(self):
        if self.selected is None:
            self.add_structure()
            return
        try:
            self.selected.notation = self.notation_input.text()
        except ValueError as e:
            self._show_error(str(e))
            return
        self._done()

    def remove_structure(self):
        if self.selected is None or self.language is None:
            return
        self.language.phonotactics.remove_syllable_structure(self.selected)
        self.selected = None
        self.notation_input.clear()
        self._done()

    def _done(self):
        self._show_error(None)
        self.refresh()
        self.changed.emit()

    def _show_error(self, message: str | None):
        self.error.setText(message or "")
        self.error.setVisible(message is not None)

class FormCheckCard(Card):
    """Checks a typed Form against the Phonotactics and shows its syllables or what it breaks."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.language: Language | None = None
        self.content.addWidget(label("CHECK A FORM", "section"))
        row = QHBoxLayout()
        self.form_input = QLineEdit(self)
        self.form_input.setObjectName("IpaInput")
        self.form_input.setPlaceholderText("Type a Form in IPA, like stata")
        self.form_input.textChanged.connect(self.check)
        row.addWidget(self.form_input, 1)
        self.content.addLayout(row)
        self.syllables = label("", "ipa", self)
        self.content.addWidget(self.syllables)
        self.result = label("", "muted", self)
        self.result.setWordWrap(True)
        self.content.addWidget(self.result)

    def set_language(self, language: Language | None):
        self.language = language
        self.check()

    def check(self):
        text = self.form_input.text()
        if self.language is None or not text.strip():
            self.syllables.setText("")
            self.result.setProperty("role", "muted")
            self.result.setText("Type a Form to split it into syllables.")
        else:
            phonotactics = self.language.phonotactics
            violations = phonotactics.check(text)
            syllables = phonotactics.syllabify(text)
            self.syllables.setText(f"/{write_syllables(syllables)}/" if syllables else "")
            self.result.setProperty("role", "error" if violations else "muted")
            if violations:
                self.result.setText("\n".join(v.message for v in violations))
            else:
                self.result.setText("Fits the Phonotactics.")
        # The role changed, so the stylesheet has to look at the label again.
        style = self.result.style()
        if style is not None:
            style.unpolish(self.result)
            style.polish(self.result)

class WordGeneratorCard(Card):
    """Generates new Forms from the Language's Syllable Structures."""

    lexicon_changed = pyqtSignal()  # pyright: ignore[reportCallIssue] PyQt6 stub bug, see pyproject.

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.language: Language | None = None
        self.content.addWidget(label("WORD GENERATOR", "section"))
        self.content.addWidget(label("Make Forms that fit the Syllable Structures and Phonotactic Constraints.", "muted", self))
        options = QHBoxLayout()
        self.count = QSpinBox(self)
        self.count.setRange(1, 1000)
        self.count.setValue(20)
        self.count.setPrefix("Forms: ")
        options.addWidget(self.count)
        self.minimum = QSpinBox(self)
        self.minimum.setRange(1, 20)
        self.minimum.setValue(1)
        self.minimum.setPrefix("Min syllables: ")
        options.addWidget(self.minimum)
        self.maximum = QSpinBox(self)
        self.maximum.setRange(1, 20)
        self.maximum.setValue(3)
        self.maximum.setPrefix("Max syllables: ")
        options.addWidget(self.maximum)
        self.seed = QLineEdit(self)
        self.seed.setPlaceholderText("Seed (optional)")
        options.addWidget(self.seed, 1)
        self.generate_button = Button("Generate", "plus", "primary", parent=self)
        self.generate_button.clicked.connect(self.generate)
        options.addWidget(self.generate_button)
        self.content.addLayout(options)
        self.forms = QListWidget(self)
        self.forms.setObjectName("EntryList")
        self.forms.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.content.addWidget(self.forms)
        actions = QHBoxLayout()
        add_selected = Button("Add Selected", "plus", parent=self)
        add_selected.clicked.connect(self.add_selected)
        actions.addWidget(add_selected)
        add_all = Button("Add All", "plus", parent=self)
        add_all.clicked.connect(self.add_all)
        actions.addWidget(add_all)
        fill = Button("Fill Unfinished", "save", parent=self)
        fill.setToolTip("Fill unfinished Entries with selected Forms, or all Forms when none are selected")
        fill.clicked.connect(self.fill_unfinished)
        actions.addWidget(fill)
        actions.addStretch()
        self.content.addLayout(actions)
        self.error = label("", "error", self)
        self.error.setWordWrap(True)
        self.error.hide()
        self.content.addWidget(self.error)

    def set_language(self, language: Language | None):
        self.language = language
        self.forms.clear()
        self._show_error(None)

    def generate(self):
        if self.language is None:
            return
        try:
            seed_text = self.seed.text().strip()
            seed = int(seed_text) if seed_text else None
            forms = self.language.generate_forms(
                self.count.value(), (self.minimum.value(), self.maximum.value()), seed
            )
        except ValueError as error:
            self.forms.clear()
            self._show_error(str(error))
            return
        self._show_error(None)
        self.forms.clear()
        for form in forms:
            syllables = self.language.phonotactics.syllabify(form)
            item = QListWidgetItem(write_syllables(syllables) if syllables is not None else str(form), self.forms)
            item.setData(Qt.ItemDataRole.UserRole, form)

    def _picked_forms(self) -> list[Form]:
        items = self.forms.selectedItems()
        if not items:
            items = [item for i in range(self.forms.count()) if (item := self.forms.item(i)) is not None]
        return [form for item in items
                if (form := item.data(Qt.ItemDataRole.UserRole)) is not None]

    def add_selected(self):
        self._add_forms(self._picked_forms())

    def add_all(self):
        forms = []
        for i in range(self.forms.count()):
            item = self.forms.item(i)
            if item is not None:
                form = item.data(Qt.ItemDataRole.UserRole)
                if form is not None:
                    forms.append(form)
        self._add_forms(forms)

    def _add_forms(self, forms: list[Form]):
        if self.language is None or not forms:
            return
        self.language.lexicon.add_generated_forms(forms)
        self._remove_forms(forms)
        self.lexicon_changed.emit()

    def fill_unfinished(self):
        if self.language is None:
            return
        forms = self._picked_forms()
        if not forms:
            return
        applied = min(len(forms), len(self.language.lexicon.unfinished()))
        self.language.lexicon.fill_unfinished(forms)
        self._remove_forms(forms[:applied])
        self.lexicon_changed.emit()

    def _remove_forms(self, forms: list[Form]):
        for index in reversed(range(self.forms.count())):
            item = self.forms.item(index)
            if item is not None and item.data(Qt.ItemDataRole.UserRole) in forms:
                self.forms.takeItem(index)

    def _show_error(self, message: str | None):
        self.error.setText(message or "")
        self.error.setVisible(message is not None)

class ConstraintsCard(Card):
    """Builds Phonotactic Constraints from Phonemes and Phoneme Classes."""

    changed = pyqtSignal()  # pyright: ignore[reportCallIssue]  PyQt6 stub bug, see pyproject.

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.language: Language | None = None
        self.atoms: list[ConstraintAtom] = []
        title = QHBoxLayout()
        title.addWidget(label("PHONOTACTIC CONSTRAINTS", "section"))
        self.count = label("0", "badge")
        title.addWidget(self.count)
        title.addStretch()
        self.content.addLayout(title)
        how_to = label("Ban a Phoneme or Class in a Syllable Part, or add several atoms to ban a sequence. "
                       "Sequences may cross syllable boundaries.", "muted", self)
        how_to.setWordWrap(True)
        self.content.addWidget(how_to)
        self.list = QListWidget(self)
        self.list.setObjectName("EntryList")
        self.list.setMinimumHeight(60)
        self.list.setMaximumHeight(150)
        self.list.currentItemChanged.connect(lambda _current, _previous: self.remove_button.setEnabled(self.list.currentItem() is not None))
        self.content.addWidget(self.list)
        self.content.addWidget(label("ADD PHONEME OR CLASS", "section", self))
        self.labels_box = QWidget(self)
        self.labels = FlowLayout(self.labels_box)
        self.content.addWidget(self.labels_box)
        self.sequence = label("No atoms selected", "ipa", self)
        self.content.addWidget(self.sequence)
        scope = QHBoxLayout()
        self.part = QComboBox(self)
        self.part.addItem("Anywhere", None)
        for value in SyllablePart:
            self.part.addItem(str(value), value)
        scope.addWidget(self.part)
        self.position = QComboBox(self)
        for value, text in ((SyllablePosition.ANY, "Any syllable"), (SyllablePosition.FIRST, "First syllable"),
                            (SyllablePosition.MIDDLE, "Middle syllable"), (SyllablePosition.LAST, "Last syllable"),
                            (SyllablePosition.ONLY, "Only syllable"), (SyllablePosition.NON_FIRST, "Non-first syllables")):
            self.position.addItem(text, value)
        scope.addWidget(self.position)
        self.mode = QComboBox(self)
        self.mode.addItem("Ban sequence", ConstraintMode.BAN)
        self.mode.addItem("Only allow sequence", ConstraintMode.ALLOW)
        scope.addWidget(self.mode)
        self.across = QCheckBox("Across syllable boundaries", self)
        self.across.setChecked(True)
        scope.addWidget(self.across)
        self.content.addLayout(scope)
        buttons = QHBoxLayout()
        self.add_button = Button("Add Constraint", "plus", "primary", parent=self)
        self.add_button.clicked.connect(self.add_constraint)
        buttons.addWidget(self.add_button)
        self.clear_button = Button("Clear Sequence", "x", parent=self)
        self.clear_button.clicked.connect(self.clear_sequence)
        buttons.addWidget(self.clear_button)
        self.remove_button = Button("Remove", "trash-2", "danger", parent=self)
        self.remove_button.clicked.connect(self.remove_constraint)
        buttons.addWidget(self.remove_button)
        buttons.addStretch()
        self.content.addLayout(buttons)
        self.error = label("", "error", self)
        self.error.setWordWrap(True)
        self.error.hide()
        self.content.addWidget(self.error)

    def set_language(self, language: Language | None):
        self.language = language
        self.clear_sequence()
        self.refresh()

    def refresh(self):
        self.list.clear()
        constraints = self.language.phonotactics.constraints if self.language is not None else []
        for constraint in constraints:
            item = QListWidgetItem(str(constraint), self.list)
            item.setData(Qt.ItemDataRole.UserRole, constraint.id)
        self.count.setText(str(len(constraints)))
        self.remove_button.setEnabled(self.list.currentItem() is not None)
        self.labels.clear()
        if self.language is None:
            return
        for phoneme_class in self.language.classes:
            value = phoneme_class.label or phoneme_class.name
            button = Button(value, parent=self.labels_box)
            button.setToolTip(f"Class: {phoneme_class.name}")
            button.clicked.connect(lambda _checked=False, value=value: self.add_atom(value, True))
            self.labels.addWidget(button)
        for symbol in self.language.inventory.symbols:
            button = Button(symbol, parent=self.labels_box)
            button.setToolTip("Phoneme")
            button.clicked.connect(lambda _checked=False, value=symbol: self.add_atom(value, False))
            self.labels.addWidget(button)

    def add_atom(self, value: str, is_class: bool):
        self.atoms.append(ConstraintAtom(value, is_class))
        self.sequence.setText(" ".join(str(atom) for atom in self.atoms))

    def clear_sequence(self):
        self.atoms = []
        self.sequence.setText("No atoms selected")

    def add_constraint(self):
        if self.language is None:
            return
        try:
            self.language.phonotactics.add_constraint(
                self.atoms, self.part.currentData(), self.position.currentData(), self.across.isChecked(), self.mode.currentData())
        except ValueError as e:
            self.error.setText(str(e))
            self.error.show()
            return
        self.error.hide()
        self.clear_sequence()
        self.refresh()
        self.changed.emit()

    def remove_constraint(self):
        item = self.list.currentItem()
        if item is None or self.language is None:
            return
        constraint_id = item.data(Qt.ItemDataRole.UserRole)
        constraint = next((c for c in self.language.phonotactics.constraints if c.id == constraint_id), None)
        if constraint is not None:
            self.language.phonotactics.remove_constraint(constraint)
        self.refresh()
        self.changed.emit()

class PhonotacticsPage(QWidget):
    """Edit one Language's Phonotactics and check Forms against them."""

    lexicon_changed = pyqtSignal()  # pyright: ignore[reportCallIssue] PyQt6 stub bug, see pyproject.

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)  # pyright: ignore[reportArgumentType]  PyQt6 stub bug, see pyproject.
        self.setObjectName("Page")
        self.language: Language | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)
        body = QWidget(scroll)
        scroll.setWidget(body)
        layout = QVBoxLayout(body)
        layout.setContentsMargins(32, 28, 32, 32)
        layout.setSpacing(16)

        self.header = PageHeader("Phonotactics", "", body)
        layout.addWidget(self.header)
        self.structures_card = StructuresCard(body)
        layout.addWidget(self.structures_card)
        self.constraints_card = ConstraintsCard(body)
        layout.addWidget(self.constraints_card)
        self.check_card = FormCheckCard(body)
        self.structures_card.changed.connect(self.check_card.check)
        self.constraints_card.changed.connect(self.check_card.check)
        layout.addWidget(self.check_card)
        self.generator_card = WordGeneratorCard(body)
        self.generator_card.lexicon_changed.connect(self.lexicon_changed)
        layout.addWidget(self.generator_card)
        layout.addStretch()

    def set_language(self, language: Language | None):
        self.language = language
        self.header.subtitle.setText(f"How the Phonemes of {language.name} combine into syllables." if language is not None else "")
        self.structures_card.set_language(language)
        self.constraints_card.set_language(language)
        self.check_card.set_language(language)
        self.generator_card.set_language(language)

    def refresh(self):
        # Classes and the inventory live on the Phonology page, so redraw anything that uses them.
        self.structures_card.refresh()
        self.constraints_card.refresh()
        self.check_card.check()
        self.generator_card.set_language(self.language)

__all__ = ["ConstraintsCard", "FormCheckCard", "PhonotacticsPage", "StructureView", "WordGeneratorCard"]

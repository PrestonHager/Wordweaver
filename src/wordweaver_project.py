# wordweaver_project.py

from collections.abc import Callable
from enum import IntEnum
from pathlib import Path

from lexicon import Definition, Entry, Form, Lexicon
from phoneme_classes import DEFAULT_CLASS_ID_BLOCK, PhonemeClass, PhonemeClasses
from phonology import Phoneme, PhonemeInventory
from wwformat import ChunkType, CorruptFileError, FileContents, NewerVersionError, ProjectFileError, UnknownChunkError, pb

class LanguageKind(IntEnum):
    """A label for a Language. It's only a description and doesn't change how the Language works."""
    # The values match the LanguageKind enum in the .proto, so they can be saved as is.
    LANGUAGE = 0
    PROTO_LANGUAGE = 1
    DIALECT = 2
    CREOLE = 3

    def __str__(self) -> str:
        return self.name.replace("_", "-").title()

class Language:
    """One conlang inside a Project, with its own Phoneme Inventory and Lexicon."""

    def __init__(self, id: int, name: str, new_id: Callable[[], int], kind: LanguageKind, default_class_ids_start: int):
        # Languages are made by Project.add_language, which hands out the IDs.
        self._id = id
        self.name = name
        self.kind = kind
        self.inventory = PhonemeInventory(new_id)
        self._classes = PhonemeClasses(self.inventory, new_id, default_class_ids_start)
        self.lexicon = Lexicon(new_id)

    @property
    def id(self) -> int:
        return self._id

    @property
    def classes(self) -> list[PhonemeClass]:
        """Every Phoneme Class in the Language, defaults first."""
        return list(self._classes)

    def add_class(self, name: str) -> PhonemeClass:
        """Make a new, empty Phoneme Class.

        :raises ValueError: If the name is empty or another Class has it.
        """
        return self._classes.add(name)

    def remove_class(self, phoneme_class: PhonemeClass):
        """Delete one of the user's own Phoneme Classes.

        :raises ValueError: If it's a default Class, or isn't in this Language.
        """
        self._classes.remove(phoneme_class)

    def get_class(self, name: str) -> PhonemeClass | None:
        return self._classes.get(name)

    def classes_of(self, symbol: str) -> list[PhonemeClass]:
        """Get every Phoneme Class a Phoneme is in."""
        return self._classes.of(symbol)

    def __repr__(self) -> str:
        return f"<Language {self.id} {self.name!r}: {', '.join(self.inventory.symbols)}>"

class Project:
    """A collection of Languages, saved to and loaded from a v1 .wwproj file."""

    def __init__(self, name: str, file: str | Path | None=None):
        self.name = name
        self.file = file
        self._languages: list[Language] = []
        # Every record in the Project takes its ID from this counter, so IDs are never reused.
        self._next_id = 1
        # Ancillary chunks from a newer app that we skipped on load, held so saving doesn't lose them.
        self._unknown_chunks = []

    @property
    def languages(self) -> list[Language]:
        return list(self._languages)

    def add_language(self, name: str, kind: LanguageKind=LanguageKind.LANGUAGE) -> Language:
        language = Language(self._new_id(), name, self._new_id, kind, self._reserve_ids(DEFAULT_CLASS_ID_BLOCK))
        self._languages.append(language)
        return language

    def remove_language(self, language: Language):
        """Remove a Language and everything in it. Its IDs are never handed out again.

        :raises ValueError: If the Language isn't in this Project.
        """
        self._languages.remove(language)

    def _new_id(self) -> int:
        return self._reserve_ids(1)

    def _reserve_ids(self, count: int) -> int:
        # Hand out `count` IDs in a row and return the first one.
        start = self._next_id
        self._next_id += count
        return start

    def save(self, file: str | Path | None=None):
        """Save the whole Project to `file`, or to the file it was last saved to or loaded from.

        :raises ValueError: If there's no file to save to.
        """
        if file is not None:
            self.file = file
        if self.file is None:
            raise ValueError("The Project doesn't have a file to save to")
        self._to_contents().write(self.file)

    @classmethod
    def load(cls, file: str | Path) -> "Project":
        """Load a Project from a v1 .wwproj file.

        :raises FileNotFoundError: If the file doesn't exist.
        :raises ProjectFileError: If the file isn't a Project file, or is damaged.
        """
        project = cls._from_contents(FileContents.read(file))
        project.file = file
        return project

    def _to_contents(self) -> FileContents:
        # Each record goes in its own table, pointing at its parent by ID.
        contents = FileContents()
        strings = contents.strings
        info = contents.get(ChunkType.PROJECT)
        info.name = strings.index(self.name)
        info.next_id = self._next_id
        for language in self._languages:
            contents.add_record(ChunkType.LANGUAGES, pb.Language(id=language.id, name=strings.index(language.name), kind=language.kind, default_class_ids_start=language._classes.default_ids_start))
            for phoneme in language.inventory:
                contents.add_record(ChunkType.PHONEMES, pb.Phoneme(id=phoneme.id, language_id=language.id, symbol=strings.index(phoneme.symbol)))
            # Default Classes are rebuilt on load, so only save the ones the user changed.
            for phoneme_class in language.classes:
                if phoneme_class.is_default and not (phoneme_class.is_renamed or phoneme_class.is_hand_edited):
                    continue
                record = pb.PhonemeClass(id=phoneme_class.id, language_id=language.id, name=strings.index(phoneme_class.name))
                if phoneme_class.is_default:
                    record.default_key = strings.index(phoneme_class._default.key)
                if not phoneme_class.is_default or phoneme_class.is_hand_edited:
                    record.hand_edited = True
                    record.phoneme_ids.extend(p.id for p in phoneme_class.phonemes)
                contents.add_record(ChunkType.PHONEME_CLASSES, record)
            for entry in language.lexicon:
                form = [strings.index(symbol) for symbol in entry.form.phonemes]
                contents.add_record(ChunkType.ENTRIES, pb.Entry(id=entry.id, language_id=language.id, form=form))
                for definition in entry.definitions:
                    glosses = [strings.index(gloss) for gloss in definition.glosses]
                    contents.add_record(ChunkType.DEFINITIONS, pb.Definition(id=definition.id, entry_id=entry.id, glosses=glosses))
        contents.unknown_chunks = list(self._unknown_chunks)
        return contents

    @classmethod
    def _from_contents(cls, contents: FileContents) -> "Project":
        strings = contents.strings
        info = contents.get(ChunkType.PROJECT)
        project = cls(strings[info.name])
        # First, rebuild the Languages, then put each Phoneme back into its Language.
        # First, make sure new IDs can't collide with loaded ones, even if next_id was missing.
        reserved = [r.default_class_ids_start + DEFAULT_CLASS_ID_BLOCK for r in contents.records(ChunkType.LANGUAGES) if r.default_class_ids_start]
        project._next_id = max([info.next_id, 1] + [id + 1 for id in contents.record_ids()] + reserved)
        # Then rebuild the Languages, then put each Phoneme back into its Language.
        languages = {}
        for record in contents.records(ChunkType.LANGUAGES):
            # A kind from a newer version that we don't know about falls back to a plain Language.
            kind = LanguageKind(record.kind) if record.kind in LanguageKind._value2member_map_ else LanguageKind.LANGUAGE
            # Files from before Phoneme Classes don't have default Class IDs yet, so give them some now.
            class_ids_start = record.default_class_ids_start or project._reserve_ids(DEFAULT_CLASS_ID_BLOCK)
            language = Language(record.id, strings[record.name], project._new_id, kind, class_ids_start)
            languages[record.id] = language
            project._languages.append(language)
        for record in contents.records(ChunkType.PHONEMES):
            if record.language_id not in languages:
                raise CorruptFileError(f"Phoneme {record.id} belongs to a Language that isn't in the file")
            languages[record.language_id].inventory._restore(Phoneme(record.id, strings[record.symbol]))
        # Then apply the user's changes to the default Classes, and put back their own Classes.
        for record in contents.records(ChunkType.PHONEME_CLASSES):
            if record.language_id not in languages:
                raise CorruptFileError(f"Phoneme Class {record.id} belongs to a Language that isn't in the file")
            classes = languages[record.language_id]._classes
            # A default Class from a newer version that we don't know about comes back as a user Class.
            phoneme_class = classes.default(strings[record.default_key]) if record.default_key else None
            if phoneme_class is None:
                phoneme_class = classes._restore(record.id, strings[record.name])
            else:
                phoneme_class._name = strings[record.name]
            if record.hand_edited:
                phoneme_class._restore_members(record.phoneme_ids)
        # Then gather each Entry's Definitions, and put the Entries back into their Lexicons.
        definitions: dict[int, list[Definition]] = {}
        for record in contents.records(ChunkType.DEFINITIONS):
            definitions.setdefault(record.entry_id, []).append(Definition(record.id, [strings[g] for g in record.glosses]))
        entry_ids = set()
        for record in contents.records(ChunkType.ENTRIES):
            if record.language_id not in languages:
                raise CorruptFileError(f"Entry {record.id} belongs to a Language that isn't in the file")
            if record.id not in definitions:
                raise CorruptFileError(f"Entry {record.id} doesn't have a Definition")
            form = Form(strings[symbol] for symbol in record.form)
            languages[record.language_id].lexicon._restore(Entry(record.id, form, definitions[record.id]))
            entry_ids.add(record.id)
        if not definitions.keys() <= entry_ids:
            raise CorruptFileError("A Definition belongs to an Entry that isn't in the file")
        project._unknown_chunks = list(contents.unknown_chunks)
        return project

__all__ = ["Language", "LanguageKind", "Project", "ProjectFileError", "CorruptFileError", "NewerVersionError", "UnknownChunkError"]

# wordweaver_project.py

from collections.abc import Callable
from enum import IntEnum
from pathlib import Path

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
    """One conlang inside a Project, with its own Phoneme Inventory."""

    def __init__(self, id: int, name: str, new_id: Callable[[], int], kind: LanguageKind=LanguageKind.LANGUAGE):
        # Languages are made by Project.add_language, which hands out the ID.
        self._id = id
        self.name = name
        self.kind = kind
        self.inventory = PhonemeInventory(new_id)

    @property
    def id(self) -> int:
        return self._id

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
        language = Language(self._new_id(), name, self._new_id, kind)
        self._languages.append(language)
        return language

    def remove_language(self, language: Language):
        """Remove a Language and everything in it. Its IDs are never handed out again.

        :raises ValueError: If the Language isn't in this Project.
        """
        self._languages.remove(language)

    def _new_id(self) -> int:
        id = self._next_id
        self._next_id += 1
        return id

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
            contents.add_record(ChunkType.LANGUAGES, pb.Language(id=language.id, name=strings.index(language.name), kind=language.kind))
            for phoneme in language.inventory:
                contents.add_record(ChunkType.PHONEMES, pb.Phoneme(id=phoneme.id, language_id=language.id, symbol=strings.index(phoneme.symbol)))
        contents.unknown_chunks = list(self._unknown_chunks)
        return contents

    @classmethod
    def _from_contents(cls, contents: FileContents) -> "Project":
        strings = contents.strings
        info = contents.get(ChunkType.PROJECT)
        project = cls(strings[info.name])
        # First, rebuild the Languages, then put each Phoneme back into its Language.
        languages = {}
        for record in contents.records(ChunkType.LANGUAGES):
            # A kind from a newer version that we don't know about falls back to a plain Language.
            kind = LanguageKind(record.kind) if record.kind in LanguageKind._value2member_map_ else LanguageKind.LANGUAGE
            language = Language(record.id, strings[record.name], project._new_id, kind)
            languages[record.id] = language
            project._languages.append(language)
        for record in contents.records(ChunkType.PHONEMES):
            if record.language_id not in languages:
                raise CorruptFileError(f"Phoneme {record.id} belongs to a Language that isn't in the file")
            languages[record.language_id].inventory._restore(Phoneme(record.id, strings[record.symbol]))
        # Finally, make sure new IDs can't collide with loaded ones, even if next_id was missing.
        project._next_id = max([info.next_id, 1] + [id + 1 for id in contents.record_ids()])
        project._unknown_chunks = list(contents.unknown_chunks)
        return project

__all__ = ["Language", "LanguageKind", "Project", "ProjectFileError", "CorruptFileError", "NewerVersionError", "UnknownChunkError"]

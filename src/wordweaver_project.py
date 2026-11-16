# wordweaver_project.py

from collections.abc import Callable
from enum import IntEnum
from pathlib import Path

from allophones import WORD_BOUNDARY, AllophoneRule, AllophoneRules, ContextSide
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
    """One conlang inside a Project, with its own Phoneme Inventory."""

    def __init__(self, id: int, name: str, new_id: Callable[[], int], kind: LanguageKind, default_class_ids_start: int):
        # Languages are made by Project.add_language, which hands out the IDs.
        self._id = id
        self.name = name
        self.kind = kind
        self.inventory = PhonemeInventory(new_id)
        self._classes = PhonemeClasses(self.inventory, new_id, default_class_ids_start)
        self._allophone_rules = AllophoneRules(self.inventory, self._classes, new_id)

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

    @property
    def allophone_rules(self) -> list[AllophoneRule]:
        return list(self._allophone_rules)

    def add_allophone_rule(self, phoneme: str, allophone: str, before: ContextSide | str=None, after: ContextSide | str=None) -> AllophoneRule:
        """Say a Phoneme is pronounced as an Allophone between two contexts, like /t/ → [ɾ] / Vowel _ Vowel.

        Each side of the context is a Phoneme (or its IPA symbol), a Phoneme Class, WORD_BOUNDARY, or None for anything.

        :raises ValueError: If a Phoneme or Class isn't in this Language, or the Allophone isn't valid IPA.
        """
        return self._allophone_rules.add(phoneme, allophone, before, after)

    def remove_allophone_rule(self, rule: AllophoneRule):
        self._allophone_rules.remove(rule)

    def allophones_of(self, symbol: str) -> list[str]:
        """Get the Allophones a Phoneme's rules give it, each once."""
        return self._allophone_rules.of(symbol)

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
            for rule in language.allophone_rules:
                contents.add_record(ChunkType.ALLOPHONE_RULES, pb.AllophoneRule(
                    id=rule.id, language_id=language.id, phoneme_id=rule.phoneme.id, allophone=strings.index(rule.allophone),
                    before=_side_to_record(rule.before), after=_side_to_record(rule.after)))
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
        # Finally, put back the Allophone Rules, now that everything they point at is loaded.
        for record in contents.records(ChunkType.ALLOPHONE_RULES):
            if record.language_id not in languages:
                raise CorruptFileError(f"Allophone Rule {record.id} belongs to a Language that isn't in the file")
            language = languages[record.language_id]
            phonemes = {p.id: p for p in language.inventory}
            classes = {c.id: c for c in language.classes}
            if record.phoneme_id not in phonemes:
                raise CorruptFileError(f"Allophone Rule {record.id} is for a Phoneme that isn't in its Language")
            before = _side_from_record(record.before, phonemes, classes, record.id)
            after = _side_from_record(record.after, phonemes, classes, record.id)
            language._allophone_rules._restore(record.id, phonemes[record.phoneme_id], strings[record.allophone], before, after)
        project._unknown_chunks = list(contents.unknown_chunks)
        return project

def _side_to_record(side: ContextSide) -> pb.ContextSide:
    if side is WORD_BOUNDARY:
        return pb.ContextSide(kind=pb.CONTEXT_WORD_BOUNDARY)
    if isinstance(side, PhonemeClass):
        return pb.ContextSide(kind=pb.CONTEXT_PHONEME_CLASS, id=side.id)
    if isinstance(side, Phoneme):
        return pb.ContextSide(kind=pb.CONTEXT_PHONEME, id=side.id)
    return pb.ContextSide()

def _side_from_record(record: pb.ContextSide, phonemes: dict[int, Phoneme], classes: dict[int, PhonemeClass], rule_id: int) -> ContextSide:
    if record.kind == pb.CONTEXT_WORD_BOUNDARY:
        return WORD_BOUNDARY
    if record.kind == pb.CONTEXT_PHONEME:
        if record.id not in phonemes:
            raise CorruptFileError(f"Allophone Rule {rule_id} has a context Phoneme that isn't in its Language")
        return phonemes[record.id]
    if record.kind == pb.CONTEXT_PHONEME_CLASS:
        if record.id not in classes:
            raise CorruptFileError(f"Allophone Rule {rule_id} has a context Class that isn't in its Language")
        return classes[record.id]
    # Anything else, including a kind from a newer version, means nothing in particular.
    return None

__all__ = ["WORD_BOUNDARY", "AllophoneRule", "Language", "LanguageKind", "Project", "ProjectFileError", "CorruptFileError", "NewerVersionError", "UnknownChunkError"]

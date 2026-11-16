# wordweaver_project.py

import os
import re
from collections.abc import Callable
from enum import IntEnum
from pathlib import Path

from allophones import WORD_BOUNDARY, AllophoneRule, AllophoneRules, ContextSide
from lexicon import ConceptReference, ConceptSource, Definition, Entry, Form, Lexicon
from lexicon_csv import export_csv
from phoneme_classes import DEFAULT_CLASS_ID_BLOCK, PhonemeClass, PhonemeClasses
from phonology import Phoneme, PhonemeInventory
from phonotactics import Phonotactics, SyllableStructure, parse_notation
from suprasegmentals import Suprasegmentals
from tags import Tag, Tags
from wwformat import ChunkType, CorruptFileError, FileContents, NewerVersionError, ProjectFileError, StringTable, UnknownChunkError, pb

DEFAULT_GLOSS_LANGUAGE = "en"

# A loose check for BCP 47 codes: an ISO 639 language, then any subtags like a region or script.
_LANGUAGE_CODE = re.compile(r"[a-z]{2,3}(-[a-z0-9]{1,8})*")

def normalize_language_code(code: str) -> str:
    """Tidy a BCP 47 code like " EN-gb " into "en-GB".

    :raises ValueError: If it doesn't look like a language code.
    """
    code = code.strip().replace("_", "-").lower()
    if not _LANGUAGE_CODE.fullmatch(code):
        raise ValueError(f"{code!r} isn't a language code like \"en\"")
    # Regions are written in capitals by convention, like "en-GB".
    primary, *subtags = code.split("-")
    return "-".join([primary] + [tag.upper() if len(tag) == 2 else tag for tag in subtags])

# Compact the file on save once patches would be more than this share of it.
COMPACT_AT = 0.25

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

    def __init__(self, id: int, name: str, new_id: Callable[[], int], kind: LanguageKind, default_class_ids_start: int, tags: Tags | None=None):
        # Languages are made by Project.add_language, which hands out the IDs.
        self._id = id
        self.name = name
        self.kind = kind
        self.inventory = PhonemeInventory(new_id)
        self._classes = PhonemeClasses(self.inventory, new_id, default_class_ids_start)
        self.lexicon = Lexicon(new_id, tags=tags)
        self._allophone_rules = AllophoneRules(self.inventory, self._classes, new_id)
        self.suprasegmentals = Suprasegmentals()
        self._phonotactics = Phonotactics(self.inventory, self._classes, new_id)

    @property
    def id(self) -> int:
        return self._id

    @property
    def phonotactics(self) -> Phonotactics:
        """The Language's Phonotactics: its Syllable Structures, and checking Forms against them."""
        return self._phonotactics

    @property
    def classes(self) -> list[PhonemeClass]:
        """Every Phoneme Class in the Language, defaults first."""
        return list(self._classes)

    def add_class(self, name: str, label: str="") -> PhonemeClass:
        """Make a new, empty Phoneme Class, with an optional short label like N for Syllable Structures.

        :raises ValueError: If the name is empty or another Class has it, or the label isn't valid or is taken.
        """
        return self._classes.add(name, label)

    def remove_class(self, phoneme_class: PhonemeClass):
        """Delete one of the user's own Phoneme Classes.

        :raises ValueError: If it's a default Class, or isn't in this Language.
        """
        self._classes.remove(phoneme_class)

    def get_class(self, name: str) -> PhonemeClass | None:
        return self._classes.get(name)

    def class_with_label(self, label: str) -> PhonemeClass | None:
        """Get the Phoneme Class with a short label, like C."""
        return self._classes.with_label(label)

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
        # Tags are shared by every Language, and removing one takes it off every Entry.
        self.tags = Tags(self._new_id, self._untag_everywhere)
        self._gloss_language = DEFAULT_GLOSS_LANGUAGE
        # What the file held after the last save or load, so saves can append only the changes.
        self._saved: FileContents | None = None
        self._saved_path: str | None = None
        self._saved_stat: tuple[int, int] | None = None

    @property
    def gloss_language(self) -> str:
        """The language Glosses are written in, as a BCP 47 code like "en". It decides which dictionary is searched."""
        return self._gloss_language

    @gloss_language.setter
    def gloss_language(self, code: str):
        """:raises ValueError: If `code` doesn't look like a BCP 47 language code."""
        self._gloss_language = normalize_language_code(code)

    @property
    def languages(self) -> list[Language]:
        return list(self._languages)

    def add_language(self, name: str, kind: LanguageKind=LanguageKind.LANGUAGE) -> Language:
        language = Language(self._new_id(), name, self._new_id, kind, self._reserve_ids(DEFAULT_CLASS_ID_BLOCK), tags=self.tags)
        self._languages.append(language)
        return language

    def remove_language(self, language: Language):
        """Remove a Language and everything in it. Its IDs are never handed out again.

        :raises ValueError: If the Language isn't in this Project.
        """
        self._languages.remove(language)

    def tagged(self, tag: Tag) -> list[Entry]:
        """Find every Entry with a Tag, in every Language."""
        return [entry for language in self._languages for entry in language.lexicon.tagged(tag)]

    def export_lexicon_csv(self, language: Language) -> str:
        """Return a Language's Lexicon as CSV text, with one row per Definition. See lexicon_csv for the columns.

        :raises ValueError: If the Language isn't in this Project.
        """
        if language not in self._languages:
            raise ValueError(f"Language {language.id} isn't in this Project")
        return export_csv(language.lexicon, self.tags)

    def _untag_everywhere(self, tag: Tag):
        for language in self._languages:
            for entry in language.lexicon.tagged(tag):
                language.lexicon.untag(entry, tag)

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
        if self._saved is not None and self._saved_path == os.path.abspath(self.file) and self._saved_stat == _stat(self.file):
            # The file already holds what we last saved, so we only append what changed since then.
            contents = self._to_contents(self._saved.strings.copy())
            patch = contents.patch_from(self._saved) or b""
            contents.patch_bytes = self._saved.patch_bytes + len(patch)
            file_size = self._saved_stat[0] + len(patch)
            # Once patches would take up more than about a quarter of the file, write it out clean instead.
            if contents.patch_bytes > file_size * COMPACT_AT:
                self.compact()
                return
            if patch:
                FileContents.append(self.file, patch)
        else:
            # The first save to a file writes the whole Project.
            self.compact()
            return
        self._remember_saved(contents)

    def compact(self):
        """Save the whole Project to its file, leaving out all the patches.

        It's written to a new file that then replaces the old one, so a crash part way through leaves the old file as it was.

        :raises ValueError: If there's no file to save to.
        """
        if self.file is None:
            raise ValueError("The Project doesn't have a file to save to")
        contents = self._to_contents(StringTable())
        contents.write(self.file)
        self._remember_saved(contents)

    def _remember_saved(self, contents: FileContents):
        # Keep what's in the file, so the next save can tell what changed.
        self._saved = contents
        self._saved_path = os.path.abspath(self.file)
        self._saved_stat = _stat(self.file)

    @classmethod
    def load(cls, file: str | Path) -> "Project":
        """Load a Project from a v1 .wwproj file.

        :raises FileNotFoundError: If the file doesn't exist.
        :raises ProjectFileError: If the file isn't a Project file, or is damaged.
        """
        contents = FileContents.read(file)
        project = cls._from_contents(contents)
        project.file = file
        # A broken patch is still sitting at the end of the file, so the next save has to write the whole file.
        if not contents.dropped_patch:
            project._remember_saved(contents)
        return project

    def _to_contents(self, strings: StringTable) -> FileContents:
        # Each record goes in its own table, pointing at its parent by ID.
        contents = FileContents(strings)
        strings = contents.strings
        info = contents.get(ChunkType.PROJECT)
        info.name = strings.index(self.name)
        info.next_id = self._next_id
        info.gloss_language = strings.index(self.gloss_language)
        for tag in self.tags:
            contents.add_record(ChunkType.TAGS, pb.Tag(id=tag.id, name=strings.index(tag.name)))
        for language in self._languages:
            suprasegmentals = language.suprasegmentals
            contents.add_record(ChunkType.LANGUAGES, pb.Language(
                id=language.id, name=strings.index(language.name), kind=language.kind, default_class_ids_start=language._classes.default_ids_start,
                stress=suprasegmentals.stress, tones=[strings.index(tone) for tone in suprasegmentals.tones], length=suprasegmentals.length))
            for phoneme in language.inventory:
                # The Frequency is left out when there isn't one, so it loads back as None.
                contents.add_record(ChunkType.PHONEMES, pb.Phoneme(id=phoneme.id, language_id=language.id, symbol=strings.index(phoneme.symbol), frequency=language.inventory.frequency(phoneme.symbol)))
            # Default Classes are rebuilt on load, so only save the ones the user changed.
            for phoneme_class in language.classes:
                if phoneme_class.is_default and not (phoneme_class.is_renamed or phoneme_class.is_hand_edited or phoneme_class.is_relabeled):
                    continue
                record = pb.PhonemeClass(id=phoneme_class.id, language_id=language.id, name=strings.index(phoneme_class.name), label=strings.index(phoneme_class.label))
                if phoneme_class.is_default:
                    record.default_key = strings.index(phoneme_class._default.key)
                if not phoneme_class.is_default or phoneme_class.is_hand_edited:
                    record.hand_edited = True
                    record.phoneme_ids.extend(p.id for p in phoneme_class.phonemes)
                contents.add_record(ChunkType.PHONEME_CLASSES, record)
            for entry in language.lexicon:
                form = [strings.index(symbol) for symbol in entry.form.phonemes]
                contents.add_record(ChunkType.ENTRIES, pb.Entry(id=entry.id, language_id=language.id, form=form, tag_ids=entry.tag_ids))
                for position, definition in enumerate(entry.definitions):
                    record = pb.Definition(
                        id=definition.id,
                        entry_id=entry.id,
                        glosses=[strings.index(gloss) for gloss in definition.glosses],
                        position=position,
                        terms=[strings.index(term) for term in definition.terms],
                        description=strings.index(definition.description),
                    )
                    reference = definition.concept_reference
                    if reference is not None:
                        record.concept_source = reference.source
                        record.concept_id = strings.index(reference.id)
                    contents.add_record(ChunkType.DEFINITIONS, record)
            for rule in language.allophone_rules:
                contents.add_record(ChunkType.ALLOPHONE_RULES, pb.AllophoneRule(
                    id=rule.id, language_id=language.id, phoneme_id=rule.phoneme.id, allophone=strings.index(rule.allophone),
                    before=_side_to_record(rule.before), after=_side_to_record(rule.after)))
            for structure in language.phonotactics.syllable_structures:
                contents.add_record(ChunkType.SYLLABLE_STRUCTURES, pb.SyllableStructure(id=structure.id, language_id=language.id, notation=strings.index(structure.notation)))
        contents.unknown_chunks = list(self._unknown_chunks)
        return contents

    @classmethod
    def _from_contents(cls, contents: FileContents) -> "Project":
        strings = contents.strings
        info = contents.get(ChunkType.PROJECT)
        project = cls(strings[info.name])
        # Files saved before the Gloss Language existed have none, so they stay English.
        try:
            project.gloss_language = strings[info.gloss_language] or DEFAULT_GLOSS_LANGUAGE
        except ValueError as e:
            raise CorruptFileError(f"The Gloss Language {strings[info.gloss_language]!r} isn't a language code") from e
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
            language = Language(record.id, strings[record.name], project._new_id, kind, class_ids_start, tags=project.tags)
            try:
                language.suprasegmentals = Suprasegmentals(record.stress, [strings[tone] for tone in record.tones], record.length)
            except ValueError as e:
                raise CorruptFileError(f"Language {record.id} has bad tones") from e
            languages[record.id] = language
            project._languages.append(language)
        for record in contents.records(ChunkType.PHONEMES):
            if record.language_id not in languages:
                raise CorruptFileError(f"Phoneme {record.id} belongs to a Language that isn't in the file")
            inventory = languages[record.language_id].inventory
            inventory._restore(Phoneme(record.id, strings[record.symbol]))
            if record.HasField("frequency"):
                try:
                    inventory.set_frequency(strings[record.symbol], record.frequency)
                except ValueError as e:
                    raise CorruptFileError(f"Phoneme {record.id} has a bad Frequency") from e
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
            # Files from before labels leave it out, so default Classes keep their default labels.
            if record.HasField("label"):
                phoneme_class._label = strings[record.label]
            if record.hand_edited:
                phoneme_class._restore_members(record.phoneme_ids)
        # Then put back the Tags, so the Entries can point at them.
        for record in contents.records(ChunkType.TAGS):
            project.tags._restore(Tag(record.id, strings[record.name]))
        # Then gather each Entry's Definitions, and put the Entries back into their Lexicons.
        # The records come in ID order, so sorting by position keeps ID order for ties, like in files saved before positions.
        definitions: dict[int, list[Definition]] = {}
        for record in sorted(contents.records(ChunkType.DEFINITIONS), key=lambda record: record.position):
            definition = Definition(
                record.id,
                [strings[g] for g in record.glosses],
                [strings[t] for t in record.terms],
                strings[record.description],
                _load_concept_reference(record, strings),
            )
            definitions.setdefault(record.entry_id, []).append(definition)
        entry_ids = set()
        for record in contents.records(ChunkType.ENTRIES):
            if record.language_id not in languages:
                raise CorruptFileError(f"Entry {record.id} belongs to a Language that isn't in the file")
            if record.id not in definitions:
                raise CorruptFileError(f"Entry {record.id} doesn't have a Definition")
            if any(project.tags.get(tag_id) is None for tag_id in record.tag_ids):
                raise CorruptFileError(f"Entry {record.id} has a Tag that isn't in the file")
            form = Form(strings[symbol] for symbol in record.form)
            languages[record.language_id].lexicon._restore(Entry(record.id, form, definitions[record.id], record.tag_ids))
            entry_ids.add(record.id)
        if not definitions.keys() <= entry_ids:
            raise CorruptFileError("A Definition belongs to an Entry that isn't in the file")
        # Then put back the Allophone Rules, now that everything they point at is loaded.
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
        # And the Syllable Structures, which only need their notation to be readable.
        for record in contents.records(ChunkType.SYLLABLE_STRUCTURES):
            if record.language_id not in languages:
                raise CorruptFileError(f"Syllable Structure {record.id} belongs to a Language that isn't in the file")
            try:
                parse_notation(strings[record.notation])
            except ValueError as e:
                raise CorruptFileError(f"Syllable Structure {record.id} isn't written right") from e
            languages[record.language_id].phonotactics._restore(record.id, strings[record.notation])
        project._unknown_chunks = list(contents.unknown_chunks)
        return project

def _stat(file: str | Path) -> tuple[int, int] | None:
    # If the file's size or modified time changed, something else wrote to it since we last did.
    try:
        stat = os.stat(file)
    except FileNotFoundError:
        return None
    return stat.st_size, stat.st_mtime_ns

def _load_concept_reference(record, strings) -> ConceptReference | None:
    # No source means no reference.
    if record.concept_source == pb.CONCEPT_SOURCE_NONE:
        return None
    # NOTE: a source from a newer version that we don't know about is dropped, like an unknown Language Kind.
    if record.concept_source not in ConceptSource._value2member_map_:
        return None
    if not strings[record.concept_id]:
        raise CorruptFileError(f"Definition {record.id} has a Concept Reference without an ID")
    return ConceptReference(ConceptSource(record.concept_source), strings[record.concept_id])

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

__all__ = ["DEFAULT_GLOSS_LANGUAGE", "Language", "LanguageKind", "Project", "ProjectFileError", "CorruptFileError", "NewerVersionError", "UnknownChunkError", "Tag", "normalize_language_code", "WORD_BOUNDARY", "AllophoneRule", "SyllableStructure"]

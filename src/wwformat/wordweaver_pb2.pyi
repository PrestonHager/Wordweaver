from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class LanguageKind(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    LANGUAGE_KIND_LANGUAGE: _ClassVar[LanguageKind]
    LANGUAGE_KIND_PROTO_LANGUAGE: _ClassVar[LanguageKind]
    LANGUAGE_KIND_DIALECT: _ClassVar[LanguageKind]
    LANGUAGE_KIND_CREOLE: _ClassVar[LanguageKind]

class ConceptSource(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CONCEPT_SOURCE_NONE: _ClassVar[ConceptSource]
    CONCEPT_SOURCE_OPEN_ENGLISH_WORDNET: _ClassVar[ConceptSource]
    CONCEPT_SOURCE_OPEN_MULTILINGUAL_WORDNET: _ClassVar[ConceptSource]
    CONCEPT_SOURCE_CONCEPTICON: _ClassVar[ConceptSource]

class ContextKind(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    CONTEXT_ANYTHING: _ClassVar[ContextKind]
    CONTEXT_WORD_BOUNDARY: _ClassVar[ContextKind]
    CONTEXT_PHONEME: _ClassVar[ContextKind]
    CONTEXT_PHONEME_CLASS: _ClassVar[ContextKind]
LANGUAGE_KIND_LANGUAGE: LanguageKind
LANGUAGE_KIND_PROTO_LANGUAGE: LanguageKind
LANGUAGE_KIND_DIALECT: LanguageKind
LANGUAGE_KIND_CREOLE: LanguageKind
CONCEPT_SOURCE_NONE: ConceptSource
CONCEPT_SOURCE_OPEN_ENGLISH_WORDNET: ConceptSource
CONCEPT_SOURCE_OPEN_MULTILINGUAL_WORDNET: ConceptSource
CONCEPT_SOURCE_CONCEPTICON: ConceptSource
CONTEXT_ANYTHING: ContextKind
CONTEXT_WORD_BOUNDARY: ContextKind
CONTEXT_PHONEME: ContextKind
CONTEXT_PHONEME_CLASS: ContextKind

class StringTable(_message.Message):
    __slots__ = ("strings",)
    STRINGS_FIELD_NUMBER: _ClassVar[int]
    strings: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, strings: _Optional[_Iterable[str]] = ...) -> None: ...

class ProjectInfo(_message.Message):
    __slots__ = ("name", "next_id", "gloss_language")
    NAME_FIELD_NUMBER: _ClassVar[int]
    NEXT_ID_FIELD_NUMBER: _ClassVar[int]
    GLOSS_LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    name: int
    next_id: int
    gloss_language: int
    def __init__(self, name: _Optional[int] = ..., next_id: _Optional[int] = ..., gloss_language: _Optional[int] = ...) -> None: ...

class Language(_message.Message):
    __slots__ = ("id", "name", "kind", "default_class_ids_start", "stress", "tones", "length")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    KIND_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_CLASS_IDS_START_FIELD_NUMBER: _ClassVar[int]
    STRESS_FIELD_NUMBER: _ClassVar[int]
    TONES_FIELD_NUMBER: _ClassVar[int]
    LENGTH_FIELD_NUMBER: _ClassVar[int]
    id: int
    name: int
    kind: LanguageKind
    default_class_ids_start: int
    stress: bool
    tones: _containers.RepeatedScalarFieldContainer[int]
    length: bool
    def __init__(self, id: _Optional[int] = ..., name: _Optional[int] = ..., kind: _Optional[_Union[LanguageKind, str]] = ..., default_class_ids_start: _Optional[int] = ..., stress: _Optional[bool] = ..., tones: _Optional[_Iterable[int]] = ..., length: _Optional[bool] = ...) -> None: ...

class LanguageTable(_message.Message):
    __slots__ = ("records",)
    RECORDS_FIELD_NUMBER: _ClassVar[int]
    records: _containers.RepeatedCompositeFieldContainer[Language]
    def __init__(self, records: _Optional[_Iterable[_Union[Language, _Mapping]]] = ...) -> None: ...

class Phoneme(_message.Message):
    __slots__ = ("id", "language_id", "symbol", "frequency")
    ID_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_ID_FIELD_NUMBER: _ClassVar[int]
    SYMBOL_FIELD_NUMBER: _ClassVar[int]
    FREQUENCY_FIELD_NUMBER: _ClassVar[int]
    id: int
    language_id: int
    symbol: int
    frequency: float
    def __init__(self, id: _Optional[int] = ..., language_id: _Optional[int] = ..., symbol: _Optional[int] = ..., frequency: _Optional[float] = ...) -> None: ...

class PhonemeTable(_message.Message):
    __slots__ = ("records",)
    RECORDS_FIELD_NUMBER: _ClassVar[int]
    records: _containers.RepeatedCompositeFieldContainer[Phoneme]
    def __init__(self, records: _Optional[_Iterable[_Union[Phoneme, _Mapping]]] = ...) -> None: ...

class PhonemeClass(_message.Message):
    __slots__ = ("id", "language_id", "name", "default_key", "hand_edited", "phoneme_ids", "label")
    ID_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DEFAULT_KEY_FIELD_NUMBER: _ClassVar[int]
    HAND_EDITED_FIELD_NUMBER: _ClassVar[int]
    PHONEME_IDS_FIELD_NUMBER: _ClassVar[int]
    LABEL_FIELD_NUMBER: _ClassVar[int]
    id: int
    language_id: int
    name: int
    default_key: int
    hand_edited: bool
    phoneme_ids: _containers.RepeatedScalarFieldContainer[int]
    label: int
    def __init__(self, id: _Optional[int] = ..., language_id: _Optional[int] = ..., name: _Optional[int] = ..., default_key: _Optional[int] = ..., hand_edited: _Optional[bool] = ..., phoneme_ids: _Optional[_Iterable[int]] = ..., label: _Optional[int] = ...) -> None: ...

class PhonemeClassTable(_message.Message):
    __slots__ = ("records",)
    RECORDS_FIELD_NUMBER: _ClassVar[int]
    records: _containers.RepeatedCompositeFieldContainer[PhonemeClass]
    def __init__(self, records: _Optional[_Iterable[_Union[PhonemeClass, _Mapping]]] = ...) -> None: ...

class Entry(_message.Message):
    __slots__ = ("id", "language_id", "form", "tag_ids")
    ID_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_ID_FIELD_NUMBER: _ClassVar[int]
    FORM_FIELD_NUMBER: _ClassVar[int]
    TAG_IDS_FIELD_NUMBER: _ClassVar[int]
    id: int
    language_id: int
    form: _containers.RepeatedScalarFieldContainer[int]
    tag_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, id: _Optional[int] = ..., language_id: _Optional[int] = ..., form: _Optional[_Iterable[int]] = ..., tag_ids: _Optional[_Iterable[int]] = ...) -> None: ...

class EntryTable(_message.Message):
    __slots__ = ("records",)
    RECORDS_FIELD_NUMBER: _ClassVar[int]
    records: _containers.RepeatedCompositeFieldContainer[Entry]
    def __init__(self, records: _Optional[_Iterable[_Union[Entry, _Mapping]]] = ...) -> None: ...

class Definition(_message.Message):
    __slots__ = ("id", "entry_id", "glosses", "position", "terms", "description", "concept_source", "concept_id")
    ID_FIELD_NUMBER: _ClassVar[int]
    ENTRY_ID_FIELD_NUMBER: _ClassVar[int]
    GLOSSES_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    TERMS_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    CONCEPT_SOURCE_FIELD_NUMBER: _ClassVar[int]
    CONCEPT_ID_FIELD_NUMBER: _ClassVar[int]
    id: int
    entry_id: int
    glosses: _containers.RepeatedScalarFieldContainer[int]
    position: int
    terms: _containers.RepeatedScalarFieldContainer[int]
    description: int
    concept_source: ConceptSource
    concept_id: int
    def __init__(self, id: _Optional[int] = ..., entry_id: _Optional[int] = ..., glosses: _Optional[_Iterable[int]] = ..., position: _Optional[int] = ..., terms: _Optional[_Iterable[int]] = ..., description: _Optional[int] = ..., concept_source: _Optional[_Union[ConceptSource, str]] = ..., concept_id: _Optional[int] = ...) -> None: ...

class DefinitionTable(_message.Message):
    __slots__ = ("records",)
    RECORDS_FIELD_NUMBER: _ClassVar[int]
    records: _containers.RepeatedCompositeFieldContainer[Definition]
    def __init__(self, records: _Optional[_Iterable[_Union[Definition, _Mapping]]] = ...) -> None: ...

class Tag(_message.Message):
    __slots__ = ("id", "name")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    id: int
    name: int
    def __init__(self, id: _Optional[int] = ..., name: _Optional[int] = ...) -> None: ...

class TagTable(_message.Message):
    __slots__ = ("records",)
    RECORDS_FIELD_NUMBER: _ClassVar[int]
    records: _containers.RepeatedCompositeFieldContainer[Tag]
    def __init__(self, records: _Optional[_Iterable[_Union[Tag, _Mapping]]] = ...) -> None: ...

class ContextSide(_message.Message):
    __slots__ = ("kind", "id")
    KIND_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    kind: ContextKind
    id: int
    def __init__(self, kind: _Optional[_Union[ContextKind, str]] = ..., id: _Optional[int] = ...) -> None: ...

class AllophoneRule(_message.Message):
    __slots__ = ("id", "language_id", "phoneme_id", "allophone", "before", "after")
    ID_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_ID_FIELD_NUMBER: _ClassVar[int]
    PHONEME_ID_FIELD_NUMBER: _ClassVar[int]
    ALLOPHONE_FIELD_NUMBER: _ClassVar[int]
    BEFORE_FIELD_NUMBER: _ClassVar[int]
    AFTER_FIELD_NUMBER: _ClassVar[int]
    id: int
    language_id: int
    phoneme_id: int
    allophone: int
    before: ContextSide
    after: ContextSide
    def __init__(self, id: _Optional[int] = ..., language_id: _Optional[int] = ..., phoneme_id: _Optional[int] = ..., allophone: _Optional[int] = ..., before: _Optional[_Union[ContextSide, _Mapping]] = ..., after: _Optional[_Union[ContextSide, _Mapping]] = ...) -> None: ...

class AllophoneRuleTable(_message.Message):
    __slots__ = ("records",)
    RECORDS_FIELD_NUMBER: _ClassVar[int]
    records: _containers.RepeatedCompositeFieldContainer[AllophoneRule]
    def __init__(self, records: _Optional[_Iterable[_Union[AllophoneRule, _Mapping]]] = ...) -> None: ...

class SyllableStructure(_message.Message):
    __slots__ = ("id", "language_id", "notation")
    ID_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_ID_FIELD_NUMBER: _ClassVar[int]
    NOTATION_FIELD_NUMBER: _ClassVar[int]
    id: int
    language_id: int
    notation: int
    def __init__(self, id: _Optional[int] = ..., language_id: _Optional[int] = ..., notation: _Optional[int] = ...) -> None: ...

class SyllableStructureTable(_message.Message):
    __slots__ = ("records",)
    RECORDS_FIELD_NUMBER: _ClassVar[int]
    records: _containers.RepeatedCompositeFieldContainer[SyllableStructure]
    def __init__(self, records: _Optional[_Iterable[_Union[SyllableStructure, _Mapping]]] = ...) -> None: ...

class PhonotacticConstraint(_message.Message):
    __slots__ = ("id", "language_id", "atoms", "atom_classes", "part", "position", "across_boundaries", "mode")
    ID_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_ID_FIELD_NUMBER: _ClassVar[int]
    ATOMS_FIELD_NUMBER: _ClassVar[int]
    ATOM_CLASSES_FIELD_NUMBER: _ClassVar[int]
    PART_FIELD_NUMBER: _ClassVar[int]
    POSITION_FIELD_NUMBER: _ClassVar[int]
    ACROSS_BOUNDARIES_FIELD_NUMBER: _ClassVar[int]
    MODE_FIELD_NUMBER: _ClassVar[int]
    id: int
    language_id: int
    atoms: _containers.RepeatedScalarFieldContainer[int]
    atom_classes: _containers.RepeatedScalarFieldContainer[bool]
    part: int
    position: int
    across_boundaries: bool
    mode: int
    def __init__(self, id: _Optional[int] = ..., language_id: _Optional[int] = ..., atoms: _Optional[_Iterable[int]] = ..., atom_classes: _Optional[_Iterable[bool]] = ..., part: _Optional[int] = ..., position: _Optional[int] = ..., across_boundaries: _Optional[bool] = ..., mode: _Optional[int] = ...) -> None: ...

class PhonotacticConstraintTable(_message.Message):
    __slots__ = ("records",)
    RECORDS_FIELD_NUMBER: _ClassVar[int]
    records: _containers.RepeatedCompositeFieldContainer[PhonotacticConstraint]
    def __init__(self, records: _Optional[_Iterable[_Union[PhonotacticConstraint, _Mapping]]] = ...) -> None: ...

class Patch(_message.Message):
    __slots__ = ("strings", "singles", "upserts", "deletes")
    STRINGS_FIELD_NUMBER: _ClassVar[int]
    SINGLES_FIELD_NUMBER: _ClassVar[int]
    UPSERTS_FIELD_NUMBER: _ClassVar[int]
    DELETES_FIELD_NUMBER: _ClassVar[int]
    strings: _containers.RepeatedScalarFieldContainer[str]
    singles: _containers.RepeatedCompositeFieldContainer[ChunkReplace]
    upserts: _containers.RepeatedCompositeFieldContainer[RecordUpsert]
    deletes: _containers.RepeatedCompositeFieldContainer[RecordDelete]
    def __init__(self, strings: _Optional[_Iterable[str]] = ..., singles: _Optional[_Iterable[_Union[ChunkReplace, _Mapping]]] = ..., upserts: _Optional[_Iterable[_Union[RecordUpsert, _Mapping]]] = ..., deletes: _Optional[_Iterable[_Union[RecordDelete, _Mapping]]] = ...) -> None: ...

class ChunkReplace(_message.Message):
    __slots__ = ("chunk_type", "message")
    CHUNK_TYPE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    chunk_type: int
    message: bytes
    def __init__(self, chunk_type: _Optional[int] = ..., message: _Optional[bytes] = ...) -> None: ...

class RecordUpsert(_message.Message):
    __slots__ = ("table", "record")
    TABLE_FIELD_NUMBER: _ClassVar[int]
    RECORD_FIELD_NUMBER: _ClassVar[int]
    table: int
    record: bytes
    def __init__(self, table: _Optional[int] = ..., record: _Optional[bytes] = ...) -> None: ...

class RecordDelete(_message.Message):
    __slots__ = ("table", "id")
    TABLE_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    table: int
    id: int
    def __init__(self, table: _Optional[int] = ..., id: _Optional[int] = ...) -> None: ...

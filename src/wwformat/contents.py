# wwformat/contents.py

import os
from pathlib import Path

from google.protobuf.message import DecodeError, Message

from wwformat import wordweaver_pb2 as pb
from wwformat.container import MAJOR_VERSION, Chunk, decode_file, encode_chunk, encode_file
from wwformat.errors import CorruptFileError, NewerVersionError, UnknownChunkError
from wwformat.migrations import migrate
from wwformat.registry import RECORD_TABLES, SINGLE_MESSAGES, ChunkType, is_critical, record_class
from wwformat.strings import StringTable

class FileContents:
    """
    Everything in a Project file as protobuf messages: the string table, the single-message chunks, and the record tables.

    This doesn't know anything about the Project model.
    The model turns itself into a FileContents to save, and reads itself back out of one to load.
    """

    def __init__(self, strings: StringTable | None=None):
        self.strings = strings if strings is not None else StringTable()
        self._singles: dict[ChunkType, Message] = {}
        # Each table maps record IDs to records, so patches can find them.
        self._records: dict[ChunkType, dict[int, Message]] = {table: {} for table in RECORD_TABLES}
        # Chunks this version doesn't know about, kept so they can be written back out later.
        self.unknown_chunks: list[Chunk] = []
        # True when the file ended in a broken patch that was left out.
        self.dropped_patch = False
        # How many bytes of the file are patches, so the Project knows when to compact.
        self.patch_bytes = 0

    def get(self, chunk_type: ChunkType) -> Message:
        """Get a single-message chunk, or an empty message if the file didn't have it."""
        if chunk_type not in self._singles:
            self._singles[chunk_type] = SINGLE_MESSAGES[chunk_type]()
        return self._singles[chunk_type]

    def add_record(self, table: ChunkType, record: Message):
        self._records[table][record.id] = record

    def records(self, table: ChunkType) -> list[Message]:
        """Get a table's records, oldest ID first."""
        return sorted(self._records[table].values(), key=lambda record: record.id)

    def record_ids(self) -> list[int]:
        """Get the ID of every record in every table."""
        return [id for records in self._records.values() for id in records]

    def encode(self) -> bytes:
        # First, turn every single message and table into a chunk.
        # These go first so every string they use is in the string table by the time we write it.
        chunks = []
        for chunk_type, message in self._singles.items():
            if chunk_type != ChunkType.STRING_TABLE:
                chunks.append(Chunk(chunk_type, message.SerializeToString()))
        for table in self._records:
            records = self.records(table)
            if records:
                message = RECORD_TABLES[table](records=records)
                chunks.append(Chunk(table, message.SerializeToString()))
        # Then put the string table in front of them.
        string_chunk = Chunk(ChunkType.STRING_TABLE, self.strings.to_message().SerializeToString())
        # Finally, the chunks we didn't understand go back out as they came in.
        return encode_file([string_chunk] + chunks + self.unknown_chunks)

    def patch_from(self, old: "FileContents") -> bytes | None:
        """
        Make the bytes of a patch chunk that turns `old` into these contents, or None if nothing changed.

        These contents have to use a copy of `old`'s string table, so the strings `old` has keep their indexes.
        """
        patch = pb.Patch(strings=self.strings.since(len(old.strings)))
        # First, any single message that changed is replaced whole.
        for chunk_type, message in self._singles.items():
            old_message = old._singles.get(chunk_type, SINGLE_MESSAGES[chunk_type]())
            if _same(message, old_message) or chunk_type == ChunkType.STRING_TABLE:
                continue
            patch.singles.add(chunk_type=chunk_type, message=message.SerializeToString())
        # Then, compare each table by ID: new or changed records are upserted, and missing ones deleted.
        for table, records in self._records.items():
            old_records = old._records[table]
            for id, record in sorted(records.items()):
                if id not in old_records or not _same(record, old_records[id]):
                    patch.upserts.add(table=table, record=record.SerializeToString())
            for id in sorted(old_records.keys() - records.keys()):
                patch.deletes.add(table=table, id=id)
        if not (patch.strings or patch.singles or patch.upserts or patch.deletes):
            return None
        return encode_chunk(Chunk(ChunkType.PATCH, patch.SerializeToString()))

    def _apply(self, patch: pb.Patch):
        self.strings.extend(patch.strings)
        for single in patch.singles:
            if single.chunk_type in SINGLE_MESSAGES:
                self._singles[ChunkType(single.chunk_type)] = _parse(SINGLE_MESSAGES[single.chunk_type], single.message)
            elif is_critical(single.chunk_type):
                raise _unknown_chunk(single.chunk_type)
        for delete in patch.deletes:
            if delete.table in RECORD_TABLES:
                self._records[ChunkType(delete.table)].pop(delete.id, None)
        for upsert in patch.upserts:
            if upsert.table in RECORD_TABLES:
                self.add_record(ChunkType(upsert.table), _parse(record_class(ChunkType(upsert.table)), upsert.record))
            elif is_critical(upsert.table):
                raise _unknown_chunk(upsert.table)
            # NOTE: a patch to an ancillary table we don't know is dropped, since there's nowhere to keep it.

    @classmethod
    def decode(cls, data: bytes) -> "FileContents":
        # A newer minor version only adds things we can skip, but a newer major version changes the layout.
        decoded = decode_file(data)
        if decoded.major > MAJOR_VERSION:
            raise NewerVersionError(f"This Project was saved by a newer version of Wordweaver (file version {decoded.major}). Update Wordweaver to open it.")
        chunks = migrate(decoded.major, decoded.chunks)
        contents = cls()
        contents.dropped_patch = decoded.dropped_patch
        contents.patch_bytes = decoded.patch_bytes
        for chunk in chunks:
            try:
                if chunk.type_id == ChunkType.STRING_TABLE:
                    contents.strings = StringTable.from_message(_parse(pb.StringTable, chunk.payload))
                elif chunk.type_id in SINGLE_MESSAGES:
                    contents.get(ChunkType(chunk.type_id)).MergeFrom(_parse(SINGLE_MESSAGES[chunk.type_id], chunk.payload))
                elif chunk.type_id in RECORD_TABLES:
                    table = _parse(RECORD_TABLES[chunk.type_id], chunk.payload)
                    for record in table.records:
                        contents.add_record(ChunkType(chunk.type_id), record)
                elif chunk.type_id == ChunkType.PATCH:
                    contents._apply(_parse(pb.Patch, chunk.payload))
                elif is_critical(chunk.type_id):
                    raise _unknown_chunk(chunk.type_id)
                else:
                    contents.unknown_chunks.append(chunk)
            except DecodeError as e:
                raise CorruptFileError(f"Chunk {chunk.type_id} couldn't be read") from e
        return contents

    def write(self, path: str | Path):
        # Write to a temporary file first, then swap it in, so a crash can't leave half a file behind.
        temp_path = f"{path}.tmp"
        with open(temp_path, "wb") as f_out:
            f_out.write(self.encode())
            f_out.flush()
            os.fsync(f_out.fileno())
        os.replace(temp_path, path)

    @staticmethod
    def append(path: str | Path, patch: bytes):
        # A crash part way through leaves a cut-off chunk at the end, which the loader drops.
        with open(path, "ab") as f_out:
            f_out.write(patch)
            f_out.flush()
            os.fsync(f_out.fileno())

    @classmethod
    def read(cls, path: str | Path) -> "FileContents":
        with open(path, "rb") as f_in:
            return cls.decode(f_in.read())

def _parse(message_class: type[Message], payload: bytes) -> Message:
    message = message_class()
    message.ParseFromString(payload)
    return message

def _same(a: Message, b: Message) -> bool:
    return a.SerializeToString(deterministic=True) == b.SerializeToString(deterministic=True)

def _unknown_chunk(type_id: int) -> UnknownChunkError:
    return UnknownChunkError(f"This Project uses something this version of Wordweaver doesn't understand (chunk {type_id}). Update Wordweaver to open it.")

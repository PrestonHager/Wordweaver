# wwformat/contents.py

import os
from pathlib import Path

from google.protobuf.message import DecodeError, Message

from wwformat import wordweaver_pb2 as pb
from wwformat.container import MAJOR_VERSION, Chunk, decode_file, encode_file
from wwformat.errors import CorruptFileError, NewerVersionError, UnknownChunkError
from wwformat.migrations import migrate
from wwformat.registry import RECORD_TABLES, SINGLE_MESSAGES, ChunkType, is_critical
from wwformat.strings import StringTable

class FileContents:
    """
    Everything in a Project file as protobuf messages: the string table, the single-message chunks, and the record tables.

    This doesn't know anything about the Project model.
    The model turns itself into a FileContents to save, and reads itself back out of one to load.
    """

    def __init__(self):
        self.strings = StringTable()
        self._singles: dict[ChunkType, Message] = {}
        self._records: dict[ChunkType, list[Message]] = {table: [] for table in RECORD_TABLES}
        # Chunks this version doesn't know about, kept so they can be written back out later.
        self.unknown_chunks: list[Chunk] = []

    def get(self, chunk_type: ChunkType) -> Message:
        """Get a single-message chunk, or an empty message if the file didn't have it."""
        if chunk_type not in self._singles:
            self._singles[chunk_type] = SINGLE_MESSAGES[chunk_type]()
        return self._singles[chunk_type]

    def add_record(self, table: ChunkType, record: Message):
        self._records[table].append(record)

    def records(self, table: ChunkType) -> list[Message]:
        """Get a table's records, oldest ID first."""
        return sorted(self._records[table], key=lambda record: record.id)

    def record_ids(self) -> list[int]:
        """Get the ID of every record in every table."""
        return [record.id for records in self._records.values() for record in records]

    def encode(self) -> bytes:
        # First, turn every single message and table into a chunk.
        # These go first so every string they use is in the string table by the time we write it.
        chunks = []
        for chunk_type, message in self._singles.items():
            if chunk_type != ChunkType.STRING_TABLE:
                chunks.append(Chunk(chunk_type, message.SerializeToString()))
        for table, records in self._records.items():
            if records:
                message = RECORD_TABLES[table](records=records)
                chunks.append(Chunk(table, message.SerializeToString()))
        # Then put the string table in front of them.
        string_chunk = Chunk(ChunkType.STRING_TABLE, self.strings.to_message().SerializeToString())
        # Finally, the chunks we didn't understand go back out as they came in.
        return encode_file([string_chunk] + chunks + self.unknown_chunks)

    @classmethod
    def decode(cls, data: bytes) -> "FileContents":
        # A newer minor version only adds things we can skip, but a newer major version changes the layout.
        major, _minor, chunks = decode_file(data)
        if major > MAJOR_VERSION:
            raise NewerVersionError(f"This Project was saved by a newer version of Wordweaver (file version {major}). Update Wordweaver to open it.")
        chunks = migrate(major, chunks)
        contents = cls()
        for chunk in chunks:
            try:
                if chunk.type_id == ChunkType.STRING_TABLE:
                    contents.strings = StringTable.from_message(_parse(pb.StringTable, chunk.payload))
                elif chunk.type_id in SINGLE_MESSAGES:
                    contents.get(ChunkType(chunk.type_id)).MergeFrom(_parse(SINGLE_MESSAGES[chunk.type_id], chunk.payload))
                elif chunk.type_id in RECORD_TABLES:
                    table = _parse(RECORD_TABLES[chunk.type_id], chunk.payload)
                    contents._records[ChunkType(chunk.type_id)].extend(table.records)
                elif is_critical(chunk.type_id):
                    raise UnknownChunkError(f"This Project uses something this version of Wordweaver doesn't understand (chunk {chunk.type_id}). Update Wordweaver to open it.")
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
        os.replace(temp_path, path)

    @classmethod
    def read(cls, path: str | Path) -> "FileContents":
        with open(path, "rb") as f_in:
            return cls.decode(f_in.read())

def _parse(message_class: type[Message], payload: bytes) -> Message:
    message = message_class()
    message.ParseFromString(payload)
    return message

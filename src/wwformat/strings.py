# wwformat/strings.py

from collections.abc import Iterable

from wwformat import wordweaver_pb2 as pb
from wwformat.errors import CorruptFileError

class StringTable:
    """Stores each unique string once. Records refer to strings by index, and index 0 is always ""."""

    def __init__(self, strings: Iterable[str]=()):
        self._strings = [""] + list(strings)
        self._indexes = {s: i for i, s in enumerate(self._strings)}

    def index(self, string: str) -> int:
        """Get the index for a string, adding it if it's new."""
        if string not in self._indexes:
            self._indexes[string] = len(self._strings)
            self._strings.append(string)
        return self._indexes[string]

    def extend(self, strings: Iterable[str]):
        # Patches add strings to the end, so their indexes have to land exactly where the saver put them.
        for string in strings:
            self._indexes.setdefault(string, len(self._strings))
            self._strings.append(string)

    def since(self, length: int) -> list[str]:
        """Get the strings added after the table was `length` long."""
        return self._strings[length:]

    def copy(self) -> "StringTable":
        return StringTable(self._strings[1:])

    def __getitem__(self, index: int) -> str:
        if not 0 <= index < len(self._strings):
            raise CorruptFileError(f"String index {index} isn't in the string table")
        return self._strings[index]

    def __len__(self) -> int:
        return len(self._strings)

    def to_message(self) -> pb.StringTable:
        return pb.StringTable(strings=self._strings[1:])

    @classmethod
    def from_message(cls, message: pb.StringTable) -> "StringTable":
        return cls(message.strings)

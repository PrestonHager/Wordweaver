# tags.py

from collections.abc import Callable, Iterator

class Tag:
    """A free label the user puts on Entries, like "animals" or "sacred words"."""

    def __init__(self, id: int, name: str):
        # Tags are made and renamed by the Project's Tags, which hands out the ID.
        self._id = id
        self._name = name

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    def __str__(self) -> str:
        return self._name

    def __repr__(self) -> str:
        return f"<Tag {self.id} {self.name!r}>"

class Tags:
    """The Project's Tags, shared by every Language. Entries refer to them by ID."""

    def __init__(self, new_id: Callable[[], int], on_remove: Callable[[Tag], None]=lambda tag: tag and None):
        """
        :param new_id: Callable[[], int]: Gives out a new record ID each time it's called, so IDs are unique in the Project.
        :param on_remove: Callable[[Tag], None]: Called with a Tag just before it's removed, so it can be taken off every Entry.
        """
        self._new_id = new_id
        self._on_remove = on_remove
        self._tags: dict[int, Tag] = {}

    def add(self, name: str) -> Tag:
        """Add a new Tag called `name`.

        :raises ValueError: If the name is blank or another Tag already has it.
        """
        tag = Tag(self._new_id(), self._check_name(name))
        self._tags[tag.id] = tag
        return tag

    def rename(self, tag: Tag, name: str):
        """Rename a Tag. Every Entry with it shows the new name, since they only keep its ID.

        :raises KeyError: If the Tag isn't in this Project.
        :raises ValueError: If the name is blank or another Tag already has it.
        """
        self._check(tag)
        tag._name = self._check_name(name, tag)

    def remove(self, tag: Tag):
        """Remove a Tag and take it off every Entry in every Language. Its ID is never handed out again.

        :raises KeyError: If the Tag isn't in this Project.
        """
        self._check(tag)
        self._on_remove(tag)
        del self._tags[tag.id]

    def get(self, id: int) -> Tag | None:
        return self._tags.get(id)

    def find(self, name: str) -> Tag | None:
        """Find a Tag by name, ignoring case and spaces around it."""
        key = name.strip().casefold()
        return next((tag for tag in self._tags.values() if tag.name.casefold() == key), None)

    def _check(self, tag: Tag):
        if self._tags.get(tag.id) is not tag:
            raise KeyError(f"Tag {tag.id} isn't in this Project")

    def _check_name(self, name: str, tag: Tag | None=None) -> str:
        # Tag names have to be unique, or you couldn't tell them apart in the filter.
        name = name.strip()
        if not name:
            raise ValueError("A Tag needs a name")
        other = self.find(name)
        if other is not None and other is not tag:
            raise ValueError(f"There's already a Tag called {other.name!r}")
        return name

    def _restore(self, tag: Tag):
        # Put back a Tag loaded from a file, keeping its ID.
        self._tags[tag.id] = tag

    def __iter__(self) -> Iterator[Tag]:
        return iter(list(self._tags.values()))

    def __len__(self) -> int:
        return len(self._tags)

    def __contains__(self, tag: Tag) -> bool:
        return self._tags.get(tag.id) is tag

__all__ = ["Tag", "Tags"]

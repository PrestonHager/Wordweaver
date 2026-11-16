# wwformat/errors.py

class ProjectFileError(Exception):
    """A file can't be read as a Wordweaver Project."""

class CorruptFileError(ProjectFileError):
    """A Wordweaver Project file is damaged."""

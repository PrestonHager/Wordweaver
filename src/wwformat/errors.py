# wwformat/errors.py

class ProjectFileError(Exception):
    """A file can't be read as a Wordweaver Project."""

class CorruptFileError(ProjectFileError):
    """A Wordweaver Project file is damaged."""

class NewerVersionError(ProjectFileError):
    """A Project file was saved by a newer version of Wordweaver."""

class UnknownChunkError(ProjectFileError):
    """A Project file has a critical chunk this version doesn't understand."""

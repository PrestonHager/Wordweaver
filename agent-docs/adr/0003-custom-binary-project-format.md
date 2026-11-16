# Projects are saved in a custom binary format

`.wwproj` files use our own binary format instead of SQLite or JSON, to keep files as small as possible.
The format has to be extendable, so new versions of the app can add to the model and bump the file version without breaking older projects.

## Layout

- **Header**: the magic number `0x87AFFA87`, then a major and a minor version.
- **Chunks**: after the header the file is a list of chunks, each one `type ID | length | payload | CRC32`.
  The type ID and length are varints, so there's no limit on the number of chunk types.
  Odd type IDs are critical (refuse to open the file if you don't know it), and even type IDs are ancillary (safe to skip).
- **Payloads**: chunk payloads are Protocol Buffers messages, so records use tagged fields and new fields can be added without a version bump.
- **Strings**: each unique string is stored once in a string table and referenced by index.
- **Compression**: large chunks are compressed with an existing library (zlib to start).
  Each payload starts with one byte saying how it's stored (0 for raw, 1 for zlib), so small chunks can stay uncompressed.
  We don't write our own compression or Huffman coding.
- **Record IDs**: every record (Entry, Phoneme, Language Change, and so on) has a stable ID that never changes, so patches can point at it.

## Saving edits

- A save appends patch chunks to the end of the file, each one inserting, replacing, or deleting records by ID, instead of rewriting the whole file.
- Loading reads the base chunks, then applies the patches in order.
- Once the patches pass a size threshold, the file is compacted: the patches are resolved and the whole file is rewritten clean.
  The user can also compact by hand.
- If a save is cut off, the CRC catches the broken patch and the file loads as it was before that patch.

## Versioning

- A minor bump adds new chunk types or new optional fields, and older apps can still open the file.
- A major bump changes the layout, and the loader migrates older files forward one version at a time.
  Saving always writes the newest version.
- An app refuses to open a file with a newer major version than it knows about.
- The first release of this format is v1.
  Files from before it aren't supported.

## What's saved

- Regular Paradigm cells and the default Phoneme Classes are rebuilt on load, not saved.
- Irregular Forms, Exceptions, and the inherited Entries in daughter Languages are saved, since Recalculation only runs when the user asks for it.
- Glyphs are saved as Bézier outlines on a 1000-unit em grid, with each point stored as a varint delta from the previous one.
- Freehand Glyphs also keep their original drawn points in an ancillary chunk, so they can be refitted with a different Smoothness.

## Considered Options

- **SQLite**: built into Python and good with large Lexicons, but it has a lot of per-file overhead, and it isn't compact for small projects.
- **JSON** (or zipped JSON): easy to read and diff, but much bigger, and the whole file is rewritten on every save.
- **Hand-written tagged fields** instead of the protobuf library: no dependency, but we'd have to write and test the encoder ourselves for the same bytes on disk.

## Consequences

- The app depends on the `protobuf` package and keeps its message definitions in `.proto` files.
- We own the chunk reader and writer, the patch and compaction logic, and a migration for every major version.
- A file with many patches loads a bit slower until it's compacted.

# ProtoHex

A VS Code extension that shows a binary file as hex and colors each byte by the protobuf field it belongs to.
It reads your `.proto` files plus a small JSON spec that describes anything around the protobuf, like Wordweaver's chunk container.

Microsoft's Hex Editor doesn't let other extensions add highlights, so this is its own read-only view.

## What you get

- A hex grid with offsets and ASCII, where each field gets its own color.
  The same field (like `Phoneme.symbol`) gets the same color everywhere.
- Tag and length bytes are dimmer than value bytes, so you can see where the payload starts.
- A tree of every field, with types and decoded values.
  Clicking a byte selects its field, and clicking the same byte again walks up to its parent.
- Hover tooltips, a details panel, and a small data inspector (u8/u16/u32, varint, binary) for the byte under the caret.
- CRC checks, `expect` checks on magic bytes, and schema mismatches all show up as problems.
  The "Next problem" button jumps between them.
- It reloads by itself when the file, the spec, or the `.proto` changes.

It's read-only.
There's no editing, and it hasn't been tried on big files, though the hex grid only draws the rows on screen.

## Install

There are two ways to do this.
Either package it and install the `.vsix`:

```bash
cd tools/vscode-protohex
npm run package
code --install-extension protohex-0.1.0.vsix
```

Or, open `tools/vscode-protohex` in VS Code and press F5 to run it in an Extension Development Host.

There are no npm dependencies, so there's nothing to `npm install`.

## Use

Right-click a file in the Explorer and pick "Open with ProtoHex".
Or, run "Reopen Editor With…" on an open file and pick ProtoHex.

To always open `.wwproj` files this way, add this to your settings:

```json
"workbench.editorAssociations": { "*.wwproj": "protohex.viewer" }
```

ProtoHex looks for any `*.protohex.json` in the workspace, and uses the first one whose `filePatterns` match the file.
You can also list spec files in the `protohex.specFiles` setting.
Click the spec name in the toolbar to pick a different spec for one file, or "No spec" to guess fields from the wire format alone.

## Writing a spec

See [wordweaver.protohex.json](wordweaver.protohex.json) for a full example.
VS Code will check spec files against [protohex.schema.json](protohex.schema.json) as you type.

For a file that's just one protobuf message, you only need this:

```json
{
  "name": "My message",
  "filePatterns": ["*.bin"],
  "proto": ["../proto/thing.proto"],
  "root": "my.pkg.Thing"
}
```

For anything with a header or framing, use `layout`, a list of fields read in order:

- `bytes` reads a fixed number of bytes. Add `expect` to check them, like magic numbers.
- `uint` reads a fixed-size integer, with `size` and `endian`.
- `varint` reads a protobuf-style varint. Add `names` to show a name from a `typeMaps` entry.
- `message` reads a protobuf message. `length` is a number, an earlier field's name, or `"rest"`. The type is either `message` or `messageFrom`, which looks it up in a `typeMaps` entry using an earlier field's value.
- `crc32` reads a 4-byte CRC32 and checks it against everything from the `from` field up to the CRC.
- `repeat` reads its `fields` over and over until the end, or `count` times.

Fields inside a `repeat` can refer to each other by name.

`bytesTypes` handles `bytes` fields that really hold a message, where a sibling field says which one.
Wordweaver's `RecordUpsert.record` is like that, since `table` says what kind of record it is.
The sibling has to come before the bytes field, which it will if its field number is lower.

## What doesn't work

- Groups (wire types 3 and 4) show up as an error.
- `.proto` options, services, and extensions are skipped. Imports work if the file is next to the importing file.
- Text fields in Wordweaver are string table indexes, and they show as plain numbers. Resolving them to the actual strings would need another spec feature.

## Checking a spec without VS Code

```bash
node test/dump.js wordweaver.protohex.json ../../test_project.wwproj
```

This prints the decoded tree and exits with an error if anything has a problem.

# The UI stays on PyQt6, with vendored Lucide icons

The old UI was a centered header, read-only text boxes, and "Edit X" buttons that opened separate windows.
We're redesigning it to look modern and be easier to use, and we're doing that in PyQt6 instead of moving to another toolkit.

## Decision

- **Toolkit**: stay on PyQt6.
  The dated look came from the layout, not from Qt.
  The model code is already separate from the UI, and the PyInstaller spec, NSIS installer, and build workflow keep working as they are.
- **Layout**: one main window with a sidebar and pages (Overview, Phonology, Lexicon) instead of pop-up editor windows.
  Edits apply to the Language right away, there's no "Save & Close" step inside a page.
- **Theme**: our own light and dark palettes in `src/theme.py`, applied as a Qt stylesheet on top of the Fusion style.
  It follows the system color scheme.
  We don't use a theme library, so there's no extra dependency or license to think about.
- **Icons**: use [Lucide](https://lucide.dev) icons wherever a button or action can have one.
  Only the icons we use are vendored into `src/icons/lucide/` as SVG files, with Lucide's ISC license next to them.
  `scripts/update_icons.py` holds the list of names and the pinned Lucide version, and downloads them.
  To add an icon, add its name to that list and run the script.
  Icons are tinted to the theme's colors when they're loaded, since Lucide draws with `currentColor`.

## Considered Options

- **Flet** (Flutter from Python): modern Material components out of the box, but it means rewriting the UI, replacing PyInstaller with `flet build`, and we weren't sure about Python 3.14 support.
- **NiceGUI** (a web UI in a native window): good if we ever want a browser version, but it's a rewrite too.
- **PyQt-Fluent-Widgets**: a Windows 11 look for Qt, but it's a large dependency and GPLv3 with a separate commercial license.
- **An icon package** like `qtawesome`: easy to use, but it ships every icon in every set, and we only need a few dozen.

## Consequences

- We own the stylesheet and the custom widgets (sidebar, phoneme chart, chips), so new pages should reuse them from `src/widgets.py` and the theme tokens instead of styling things one off.
- New icons need a run of `scripts/update_icons.py`, and the SVGs are committed.

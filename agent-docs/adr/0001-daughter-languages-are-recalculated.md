# Daughter languages are recalculated from their parents

A daughter Language's inherited Entries are computed from its parents' Lexicons by running the Language Changes on each Descent link.
We picked this over copying the parent once, so that you can go back and change a Proto-Language and have the changes flow down.
Recalculation only happens when the user explicitly asks for it, so a daughter never changes under you without warning.

## Considered Options

- **Snapshot**: apply the Changes once and copy the result into an independent daughter.
  This is simpler, but any later edit to the parent would have to be redone by hand in every daughter.

## Consequences

- A daughter can be out of date with its parents until it's recalculated, and the app needs to show that.
- Hand edits to a computed Entry are stored as exceptions so they survive a recalculation.
- A daughter can be detached from a parent, which turns its inherited Entries into ordinary ones.

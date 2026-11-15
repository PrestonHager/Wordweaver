# Domain Docs

How the engineering skills should use this repo's domain docs when exploring the code.

`docs/` is only for user documentation (the Sphinx site on Read the Docs).
Agent docs, ADRs, and the domain diagram all live in `agent-docs/` instead.

## Before exploring, read these

- **`CONTEXT.md`** at the repo root: the glossary.
- **`agent-docs/domain-diagram.md`**: a Mermaid diagram of how the glossary terms relate.
- **`agent-docs/adr/`**: read the ADRs that touch the area you're about to work in.

If any of these don't exist, **proceed silently**.
Don't flag their absence, and don't suggest creating them upfront.
The `/domain-modeling` skill (reached through `/grill-with-docs` and `/improve-codebase-architecture`) creates them lazily when terms or decisions actually get resolved.

## File structure

This is a single-context repo:

```
/
├── CONTEXT.md
├── agent-docs/
│   ├── domain-diagram.md
│   └── adr/
│       └── 0001-daughter-languages-are-recalculated.md
├── docs/            ← user docs only
└── src/
```

## Keep the diagram in sync

Whenever you add, rename, or remove a term in `CONTEXT.md`, or change how two terms relate, update `agent-docs/domain-diagram.md` in the same change.
Class names in the diagram are the glossary terms with the spaces removed.

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in `CONTEXT.md`.
Don't drift to synonyms the glossary explicitly avoids.

If the concept you need isn't in the glossary yet, that's a signal.
Either you're inventing language the project doesn't use (reconsider), or there's a real gap (note it for `/domain-modeling`).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0001 (daughter languages are recalculated), but worth reopening because…_

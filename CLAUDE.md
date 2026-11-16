# Wordweaver

`docs/` is only for user documentation.
Agent docs go in `agent-docs/`.

## Agent skills

### Issue tracker

Issues are tracked in GitHub Issues on PrestonHager/Wordweaver, using the `gh` CLI. See `agent-docs/issue-tracker.md`.

### Triage labels

Uses the default labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `agent-docs/triage-labels.md`.

### Domain docs

Single-context: `CONTEXT.md` at the repo root, with the domain diagram and ADRs in `agent-docs/`. See `agent-docs/domain.md`.

## UI

The UI is PyQt6 with a sidebar and pages, our own theme in `src/theme.py`, and Lucide icons vendored into `src/icons/lucide/`.
Reuse the widgets in `src/widgets.py` and the theme tokens for new UI.
To add an icon, add its name to `scripts/update_icons.py` and run it.
See `agent-docs/adr/0004-ui-stays-on-pyqt6-with-lucide-icons.md`.

# Dev Buddy — module layout and design pattern

This document describes how the app is split so new features stay consistent.

**For Cursor:** the same constraints are enforced automatically via `.cursor/rules/devbuddy-architecture.mdc` (`alwaysApply: true`), so agents see the pattern in every chat. Use this document when you want diagrams, the full module table, dependency rules, or onboarding notes for humans.

## Goals

- **Thin entry point** — `main.py` only configures CustomTkinter and starts the app.
- **One package** — All application logic lives under `devbuddy/` so imports are predictable.
- **Separation of concerns** — UI chrome, domain logic, I/O, and OS integration live in different modules.
- **Easy ingestion** — New screens or utilities are new files (or subpackages), not a growing monolith.

## Repository layout

| Location | Role |
|----------|------|
| `main.py` | Entry only: `ctk` theme + `DevLauncherApp` + `mainloop()`. |
| `devbuddy/` | Installable-style package: real application code. |
| `config.json`, icons, `icon_gen.py` | Repo-root assets; paths resolve from package code via `devbuddy/config.py` (`_ROOT`). |
| `requirements.txt`, scripts (`run.bat`, `create_shortcut.py`) | Tooling; not imported by the GUI package. |

## Package map (`devbuddy/`)

| Module | Responsibility |
|--------|----------------|
| `theme.py` | Colors, spacing, layout constants (`CARD_PALETTE`, `NEON_*`, padding). No behavior. |
| `utils.py` | Pure helpers (color math, `virtual_screen_bbox`). No Tk, no I/O. |
| `config.py` | `CONFIG_PATH`, `load_config` / `save_config`, normalization of stored shapes. |
| `playlists.py` | Spotify/YouTube URL rules and accents. No UI. |
| `launcher_ops.py` | Cursor / Visual Studio launch and process close. Uses `tkinter.messagebox` for errors only. |
| `widgets.py` | Reusable CustomTkinter factories (`neon_button`, `styled_entry`, …). |
| `eyedropper.py` | `EyedropperOverlay` (plain Tk + canvas). Self-contained tool window. |
| `dialogs/` | Modal `CTkToplevel` dialogs (`ProjectDialog`, `PlaylistDialog`). Each dialog in its own file; `dialogs/__init__.py` re-exports. |
| `app.py` | `DevLauncherApp` — shell, navigation, and module-specific UI wiring. |
| `__init__.py` | Public surface: `from devbuddy import DevLauncherApp`. |

**Dependency direction (allowed):**

```text
main.py  →  app.py
app.py   →  theme, utils, config, widgets, dialogs, playlists, launcher_ops, eyedropper
dialogs  →  theme, widgets, playlists (and stdlib / ctk)
config   →  theme, playlists (for migration / defaults)
widgets  →  theme only (keep widgets dumb)
```

Avoid: `config` importing `app`, `theme` importing `app`, or circular imports between `dialogs` and `app` (dialogs should not import `DevLauncherApp`).

## Adding a new **feature area** (e.g. another sidebar module)

1. **Constants** — If it needs colors or spacing only, extend `theme.py` (or a new `devbuddy/<feature>_theme.py` if it grows large).
2. **Logic without UI** — New module at `devbuddy/<feature>.py` (e.g. `notifications.py`) with pure functions or side-effectful helpers as appropriate.
3. **Reusable controls** — Add factories to `widgets.py` or `devbuddy/widgets_<area>.py` if `widgets.py` gets crowded.
4. **Modal UI** — New file under `devbuddy/dialogs/` + export in `dialogs/__init__.py`.
5. **Main window wiring** — In `app.py`: new frame, `_build_<feature>_module`, nav button in `_build_ui` / `_select_module`.

Keep `app.py` organized by grouping methods (e.g. picker methods together, music methods together).

## Adding a small **behavior** to an existing area

- Launcher-only → `launcher_ops.py` or `app.py` if purely UI orchestration.
- Persistence → `config.py` + schema updates in `load_config` / normalization.
- Shared styling → `theme.py` or `widgets.py`.

## Imports

- Inside the package use **absolute** imports: `from devbuddy.theme import BG`.
- Repo-root helpers: `from icon_gen import ICON_PATH` from `app.py` (run from repo root; `main.py` stays the supported entry).
- Prefer **not** to add `sys.path` hacks; run as `python main.py` from the project root.

## Testing changes

Run from repo root:

```bash
python main.py
```

Fix import errors immediately; avoid lazy imports unless breaking a real circular dependency.

## Anti-patterns

- Dumping new UI into `app.py` without extracting dialogs or helpers when they exceed ~100 lines or are reused.
- Putting `load_config` / file paths in random modules — keep I/O in `config.py`.
- Duplicating palette constants outside `theme.py`.

---

## Making the AI follow this without opening this file

Cursor loads **project rules** from `.cursor/rules/*.mdc`. This repo includes `devbuddy-architecture.mdc`, which summarizes the layout and constraints. Keep that file **short and actionable**; expand detail here in `docs/module-pattern.md` when the pattern evolves.

Optional: mention in team onboarding that agents should follow `.cursor/rules/` + this doc for large refactors.

---
name: bridge-fidelity-demo
description: Tiny demo skill that proves native-only fidelity (sys.argv, sibling resource files, real stdin, and a pip dependency) — the exact things the Taiga browser sandbox cannot do.
---

# Bridge Fidelity Demo

A minimal skill whose only job is to **prove** what the Taiga Skill Bridge
unlocks over the web sandbox. It ships two scripts:

## `scripts/transform.py`
Reads three inputs at once and prints a combined result:

- **`sys.argv[1]`** — a real command-line argument.
- **`resources/data.txt`** — a sibling resource file, read by a **relative**
  path (only resolvable because the bridge runs the script with `cwd` set to the
  skill directory and lays out `resources/` next to `scripts/`).
- **stdin** — real piped text.

Run it through the bridge with an `argv` value and some `input` (stdin); the
output reflects all three. In Pyodide there is no `argv`, no sibling file on the
virtual FS, and stdin is emulated; on the owner-server `python -I -c` path the
working directory is an empty tempdir with closed stdin — so neither can produce
this result.

## `scripts/deps_demo.py`
Imports the third-party **`requests`** package (declared in `requirements.txt`).
The bridge builds a **per-skill venv**, `pip install`s the requirements, and runs
this script with that venv's Python — so the import succeeds. Base Pyodide cannot
load this package.

### Files
- `scripts/transform.py` — argv + sibling resource + stdin demo
- `scripts/deps_demo.py` — pip-dependency (venv) demo
- `resources/data.txt` — the sibling resource read by `transform.py`
- `requirements.txt` — declares `requests` for the venv path

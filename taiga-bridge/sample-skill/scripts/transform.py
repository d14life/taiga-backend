#!/usr/bin/env python3
"""transform.py — the canonical "browser sandbox CANNOT run this" demo.

It exercises the THREE fidelity gaps the Taiga web sandbox (Pyodide) and the
owner-server `python -I -c <code>` path cannot cover, all at once:

  1. sys.argv[1]            — a real command-line argument
  2. resources/data.txt     — a SIBLING resource file, read by RELATIVE path
                              (works only because cwd == the skill dir)
  3. stdin                  — real text piped into the process

It prints a combined, human-readable result plus a machine-readable JSON line so
the Taiga web app can both show it and parse it.
"""

import json
import sys
from pathlib import Path


def main() -> int:
    # 1) argv — first CLI argument (the thing the empty-tempdir server path drops)
    arg = sys.argv[1] if len(sys.argv) > 1 else "(no argv[1])"

    # 2) sibling resource — read by RELATIVE path. This only resolves because the
    #    bridge runs us with cwd = the skill directory and materializes resources/
    #    next to scripts/. In Pyodide there is no such file on the virtual FS.
    here = Path(__file__).resolve().parent           # .../sample-skill/scripts
    resource_path = here.parent / "resources" / "data.txt"
    resource = resource_path.read_text("utf-8").strip()

    # 3) stdin — real piped input. The server `-c` path gives a closed stdin.
    stdin_data = sys.stdin.read().strip()

    combined = f"[{arg}] {resource} :: {stdin_data}"

    print("Taiga Skill Bridge — native fidelity proof")
    print(f"  argv[1]            = {arg}")
    print(f"  resources/data.txt = {resource}   (read via relative sibling path)")
    print(f"  stdin              = {stdin_data}")
    print(f"  COMBINED           = {combined}")
    # machine-readable line (single JSON object) so the web app can parse it
    print("RESULT_JSON " + json.dumps({
        "argv1": arg,
        "resource": resource,
        "stdin": stdin_data,
        "combined": combined,
        "cwd": str(Path.cwd()),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

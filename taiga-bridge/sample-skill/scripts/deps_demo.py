#!/usr/bin/env python3
"""deps_demo.py — proves the PER-SKILL VENV + PIP path.

Imports a real third-party pip package (`requests`) that does NOT exist in
Pyodide's default runtime and is NOT in the stdlib. The bridge sees this skill's
requirements.txt, builds a per-skill venv, pip-installs into it, and runs THIS
script with that venv's python — so the import succeeds.

It does NOT make a network call (the import alone proves the package loaded);
it just reports the installed version, which is enough to prove the venv path.
"""

import sys


def main() -> int:
    try:
        import requests  # third-party; absent from stdlib AND from base Pyodide
    except Exception as e:  # pragma: no cover
        print(f"IMPORT_FAILED: {e}", file=sys.stderr)
        return 1

    # argv still works here too (native fidelity), default if absent.
    label = sys.argv[1] if len(sys.argv) > 1 else "deps-ok"
    print("Taiga Skill Bridge — pip dependency proof")
    print(f"  imported third-party package: requests {requests.__version__}")
    print(f"  running under interpreter:    {sys.executable}")
    print(f"  label(argv[1]):               {label}")
    print(f"PIP_RESULT requests=={requests.__version__} interp={sys.executable}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

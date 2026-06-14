#!/usr/bin/env python3
"""Taiga Skill Bridge — a LOCAL native skill-runner daemon.

WHAT THIS IS
------------
A tiny localhost HTTP daemon that lets the Taiga web app execute installed
skills with FULL native fidelity on the USER'S OWN machine — exactly the way
Claude desktop runs skills. It runs the skill's REAL script with real Python,
real pip packages, real sys.argv, sibling resource files, real stdin, real
filesystem, and (optionally) a shell — everything a browser sandbox (Pyodide)
and the owner-server `python -I -c <code>` path cannot do.

WHY IT EXISTS (the fidelity gap it closes)
------------------------------------------
Taiga's existing web skill execution is deliberately limited (anti-RCE):
  * browser-WASM (Pyodide) cannot load arbitrary pip packages, has no real FS,
    no real argv, only an emulated stdin;
  * the owner-server path runs `python -I -c <code>` in an EMPTY tempdir — no
    argv, no cwd, no sibling resources, no stdin.
A user-run LOCAL daemon removes all of that. The web app detects this bridge on
localhost (GET /health) and routes "native" skills here (POST /run with token);
it falls back to WASM / cloud-sandbox when the bridge is not running.

SECURITY MODEL (this is RCE-by-design, on the user's own box)
-------------------------------------------------------------
Running a skill's bundled script natively IS arbitrary code execution — that is
the whole point (same as Claude desktop running a skill). To make that explicit
and as safe as a local tool can be:
  * binds 127.0.0.1 ONLY — never 0.0.0.0, never exposed to the network;
  * prints a fresh random session TOKEN on startup; every endpoint except
    /health requires header  X-Bridge-Token: <token>;
  * NO auto-run, NO background/scheduled execution — code runs ONLY in response
    to an explicit POST /run that the running Taiga tab made on the user's
    behalf;
  * CORS is locked to http://localhost:3000 (Taiga dev) + one configurable prod
    origin, with credentials; OPTIONS preflight handled;
  * a startup warning makes the trust model obvious: only run skills you trust.

Pure Python 3 stdlib for the daemon itself (no pip deps). It RUNS skills that
may pip-install into a per-skill venv.
"""

from __future__ import annotations

import base64
import json
import os
import platform
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# Reuse Taiga's static skill analyzer when it's importable (sibling mostik-ai dir),
# so the bridge classifies runtime/deps the SAME way the web app + backend do.
# Soft import — the bridge works fully without it (deps still come from the
# skill's requirements.txt and the explicit body.env/argv).
_MOSTIK_DIR = Path(__file__).resolve().parent.parent
if str(_MOSTIK_DIR) not in sys.path:
    sys.path.insert(0, str(_MOSTIK_DIR))
try:
    from skill_caps import analyze_skill as _analyze_skill  # type: ignore
except Exception:  # pragma: no cover - analyzer is a nice-to-have, not required
    _analyze_skill = None


# ───────────────────────────── config / limits ─────────────────────────────

VERSION = "0.1.0"
HOST = "127.0.0.1"                       # LOCALHOST ONLY. Never change to 0.0.0.0.
DEFAULT_PORT = 8787

RUN_TIMEOUT_SEC = 120                    # hard wall-clock cap on a single skill run
PIP_TIMEOUT_SEC = 240                    # cap on per-skill venv pip install
OUTPUT_CAP_BYTES = 256 * 1024            # cap stdout/stderr each (anti-flood)
PRODUCED_FILE_CAP_BYTES = 2 * 1024 * 1024  # per produced-file cap we return
PRODUCED_FILES_TOTAL_CAP = 8 * 1024 * 1024  # total bytes of produced files returned
PRODUCED_FILES_MAX_COUNT = 40            # max number of produced files returned
SKILL_FILE_MAX_BYTES = 2 * 1024 * 1024   # cap on a single materialized skill file
SKILL_TOTAL_MAX_BYTES = 16 * 1024 * 1024  # cap on a whole materialized skill folder

# Allowed browser origins for CORS (Taiga dev + a configurable prod origin).
DEV_ORIGIN = "http://localhost:3000"
ALT_DEV_ORIGIN = "http://127.0.0.1:3000"
PROD_ORIGIN = os.environ.get("TAIGA_BRIDGE_ORIGIN", "").strip()
ALLOWED_ORIGINS = {o for o in (DEV_ORIGIN, ALT_DEV_ORIGIN, PROD_ORIGIN) if o}

# Where we cache materialized skills + their venvs (per-skill, reused across runs).
CACHE_ROOT = Path(
    os.environ.get("TAIGA_BRIDGE_CACHE", "")
    or (Path(tempfile.gettempdir()) / "taiga-bridge-cache")
)

# Session token: fresh per process start. Overridable via env for power users who
# want a stable token across restarts (e.g. pinned in the Taiga settings UI).
SESSION_TOKEN = os.environ.get("TAIGA_BRIDGE_TOKEN", "").strip() or secrets.token_urlsafe(24)

SCRIPT_EXTS = (".py", ".js", ".mjs", ".sh", ".bash")
# Treat these as text when returning produced files; everything else → base64.
_TEXT_EXTS = (
    ".txt", ".md", ".json", ".csv", ".tsv", ".yaml", ".yml", ".toml", ".cfg",
    ".ini", ".xml", ".html", ".htm", ".py", ".js", ".mjs", ".sh", ".bash",
    ".log", ".svg", ".rst", ".env", ".sql",
)


def _slug(name: str) -> str:
    import re
    return (re.sub(r"[^a-z0-9_-]", "", str(name or "").lower().replace(" ", "-"))[:60]
            or "skill")


def _safe_join(base: Path, rel: str) -> Path | None:
    """Join rel under base, refusing path traversal (.. / absolute escapes)."""
    rel = str(rel or "").lstrip("/\\")
    target = (base / rel)
    try:
        target.resolve().relative_to(base.resolve())
    except Exception:
        return None
    return target


# ───────────────────────────── skill materialization ─────────────────────────────

def _materialize_skill(skill: dict) -> tuple[Path | None, str | None]:
    """Write a skill's files into a cached per-skill dir, PRESERVING structure
    (scripts/, resources/, references/...), so sibling files are readable at run
    time. Returns (skill_dir, error).

    `skill` is either:
      { "name": str, "files": { "<relpath>": "<content>", ... } }   (preferred)
    or it carries a "skill_dir" that already exists on disk (we use it as-is).
    """
    # Case 1: caller points us at an existing on-disk skill dir.
    sdir_in = skill.get("skill_dir")
    if sdir_in:
        p = Path(sdir_in)
        if p.is_dir():
            return p, None
        return None, f"skill_dir does not exist: {sdir_in}"

    files = skill.get("files")
    if not isinstance(files, dict) or not files:
        return None, "skill.files must be a non-empty { relpath: content } map (or pass skill_dir)"

    name = _slug(skill.get("name") or "skill")
    sdir = CACHE_ROOT / "skills" / name
    # Clean prior materialization of the SAME skill (idempotent reinstall), but
    # keep the venv dir if it exists (reused across runs) — handled separately.
    src_dir = sdir / "src"
    if src_dir.exists():
        shutil.rmtree(src_dir, ignore_errors=True)
    src_dir.mkdir(parents=True, exist_ok=True)

    total = 0
    for rel, content in files.items():
        dest = _safe_join(src_dir, rel)
        if dest is None:
            return None, f"unsafe path in skill.files: {rel!r}"
        # content may be {"b64": "..."} for binary, or a plain string for text.
        if isinstance(content, dict) and "b64" in content:
            try:
                data = base64.b64decode(content["b64"])
            except Exception:
                return None, f"bad base64 for {rel!r}"
        else:
            data = str(content).encode("utf-8")
        if len(data) > SKILL_FILE_MAX_BYTES:
            return None, f"file too large (> {SKILL_FILE_MAX_BYTES} bytes): {rel}"
        total += len(data)
        if total > SKILL_TOTAL_MAX_BYTES:
            return None, f"skill folder exceeds total cap ({SKILL_TOTAL_MAX_BYTES} bytes)"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)

    return src_dir, None


def _skill_cache_base(skill_dir: Path) -> Path:
    """The per-skill cache base (parent of src/), where we also park the venv."""
    # If skill_dir is our materialized .../skills/<name>/src → base is its parent.
    if skill_dir.name == "src" and skill_dir.parent.parent.name == "skills":
        return skill_dir.parent
    # External skill_dir: derive a stable cache base from its absolute path slug.
    key = _slug(str(skill_dir.resolve()).replace("/", "-"))
    return CACHE_ROOT / "skills" / ("ext-" + key)


# ───────────────────────────── dependency / venv handling ─────────────────────────────

def _collect_requirements(skill_dir: Path, declared_deps) -> list[str]:
    """Gather pip requirements for a skill: from requirements.txt (if present) +
    any explicitly declared deps in the request body. Returns a de-duped list of
    requirement strings (order preserved, requirements.txt first)."""
    reqs: list[str] = []
    seen = set()

    def _add(line: str):
        line = line.strip()
        if not line or line.startswith("#"):
            return
        if line in seen:
            return
        seen.add(line)
        reqs.append(line)

    req_file = skill_dir / "requirements.txt"
    if req_file.is_file():
        try:
            for line in req_file.read_text("utf-8", "ignore").splitlines():
                _add(line)
        except Exception:
            pass

    if isinstance(declared_deps, (list, tuple)):
        for d in declared_deps:
            if isinstance(d, str):
                _add(d)

    return reqs


def _venv_python(venv_dir: Path) -> Path:
    """Path to the venv's python executable (POSIX vs Windows layout)."""
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _ensure_venv(cache_base: Path, reqs: list[str]) -> tuple[Path | None, list[str], str | None]:
    """Ensure a per-skill venv exists with `reqs` installed (reused across runs).

    Strategy: keep a manifest of installed requirement strings beside the venv.
    If the requested set matches the manifest, skip pip entirely (fast reuse).
    Otherwise (re)install the requested set into the existing/new venv.

    Returns (venv_python_path, deps_installed, error). If reqs is empty, returns
    (None, [], None) — the skill runs against the system python3.
    """
    if not reqs:
        return None, [], None

    venv_dir = cache_base / "venv"
    manifest = cache_base / "venv.reqs.json"
    vpy = _venv_python(venv_dir)

    # Fast path: venv exists AND installed set already matches the requested set.
    if vpy.exists() and manifest.exists():
        try:
            prev = json.loads(manifest.read_text("utf-8"))
            if isinstance(prev, list) and set(prev) == set(reqs):
                return vpy, list(reqs), None
        except Exception:
            pass  # corrupt manifest → fall through and reinstall

    # Create the venv if missing (with pip).
    if not vpy.exists():
        try:
            import venv as _venv_mod
            _venv_mod.EnvBuilder(with_pip=True, clear=False).create(str(venv_dir))
        except Exception as e:
            return None, [], f"failed to create venv: {e}"
        vpy = _venv_python(venv_dir)
        if not vpy.exists():
            return None, [], "venv created but python executable missing"

    # Install the requested requirements.
    cmd = [str(vpy), "-m", "pip", "install", "--disable-pip-version-check",
           "--no-input", *reqs]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=PIP_TIMEOUT_SEC,
        )
    except subprocess.TimeoutExpired:
        return None, [], f"pip install timed out after {PIP_TIMEOUT_SEC}s"
    except Exception as e:
        return None, [], f"pip install failed to start: {e}"

    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip()[-1200:]
        return None, [], f"pip install failed (exit {proc.returncode}): {tail}"

    # Record the manifest for fast reuse next time.
    try:
        manifest.write_text(json.dumps(sorted(set(reqs))), "utf-8")
    except Exception:
        pass

    return vpy, list(reqs), None


# ───────────────────────────── produced-file diffing ─────────────────────────────

def _snapshot(dir_path: Path) -> dict[str, tuple[float, int]]:
    """Map relpath -> (mtime, size) for every regular file under dir_path,
    skipping the venv (huge, irrelevant) and python caches."""
    out: dict[str, tuple[float, int]] = {}
    base = dir_path.resolve()
    for dp, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in (
            "venv", ".venv", "__pycache__", ".git", "node_modules",
        )]
        for fn in filenames:
            fp = Path(dp) / fn
            try:
                st = fp.stat()
                rel = str(fp.resolve().relative_to(base))
                out[rel] = (st.st_mtime, st.st_size)
            except Exception:
                continue
    return out


def _looks_text(path: Path) -> bool:
    if path.suffix.lower() in _TEXT_EXTS:
        return True
    # Sniff: small files with no NUL byte are treated as text.
    try:
        chunk = path.read_bytes()[:4096]
    except Exception:
        return False
    return b"\x00" not in chunk


def _collect_produced(skill_dir: Path, before: dict, after: dict) -> list[dict]:
    """Return files that were created or modified during the run (before→after
    diff), as [{path, text|b64, bytes, truncated?}]. Caps count + sizes."""
    produced: list[dict] = []
    total = 0
    changed = []
    for rel, meta in after.items():
        if rel not in before or before[rel] != meta:
            changed.append(rel)
    changed.sort()

    for rel in changed:
        if len(produced) >= PRODUCED_FILES_MAX_COUNT:
            break
        fp = _safe_join(skill_dir, rel)
        if fp is None or not fp.is_file():
            continue
        try:
            size = fp.stat().st_size
        except Exception:
            continue
        entry: dict = {"path": rel, "bytes": size}
        read_n = min(size, PRODUCED_FILE_CAP_BYTES)
        if total + read_n > PRODUCED_FILES_TOTAL_CAP:
            entry["skipped"] = "total produced-file cap reached"
            produced.append(entry)
            break
        try:
            data = fp.read_bytes()[:PRODUCED_FILE_CAP_BYTES]
        except Exception:
            continue
        truncated = size > PRODUCED_FILE_CAP_BYTES
        if _looks_text(fp):
            entry["text"] = data.decode("utf-8", "replace")
        else:
            entry["b64"] = base64.b64encode(data).decode("ascii")
        if truncated:
            entry["truncated"] = True
        total += len(data)
        produced.append(entry)
    return produced


# ───────────────────────────── the actual native run ─────────────────────────────

def run_skill(body: dict) -> dict:
    """Execute one skill script NATIVELY. Body shape (see README):

        {
          "skill":  { "name": str, "files": { relpath: content } }  | { "skill_dir": str },
          "script": "scripts/transform.py",       # relpath within the skill dir
          "input":  "stdin text",                 # optional → real process stdin
          "argv":   ["arg1", "arg2"],             # optional → real sys.argv[1:]
          "env":    { "KEY": "VAL" },              # optional → added to real env
          "deps":   ["requests==2.x", ...]        # optional extra pip deps
        }

    Returns:
        { ok, exit, stdout, stderr, files:[{path,text|b64}], runtime:"native-bridge",
          deps_installed:[...], skill_dir, duration_ms, ... }
    """
    skill = body.get("skill")
    if not isinstance(skill, dict):
        return {"ok": False, "error": "missing 'skill' object"}
    script_rel = body.get("script")
    if not script_rel or not isinstance(script_rel, str):
        return {"ok": False, "error": "missing 'script' (relative path to the script to run)"}

    skill_dir, err = _materialize_skill(skill)
    if err:
        return {"ok": False, "error": err}
    assert skill_dir is not None

    script_path = _safe_join(skill_dir, script_rel)
    if script_path is None:
        return {"ok": False, "error": f"unsafe script path: {script_rel!r}"}
    if not script_path.is_file():
        return {"ok": False, "error": f"script not found in skill: {script_rel}"}

    ext = script_path.suffix.lower()
    if ext not in SCRIPT_EXTS:
        return {"ok": False, "error": f"not an executable script (.py/.js/.mjs/.sh/.bash): {script_rel}"}

    # ── dependencies → per-skill venv (reused across runs) ──
    cache_base = _skill_cache_base(skill_dir)
    cache_base.mkdir(parents=True, exist_ok=True)
    reqs = _collect_requirements(skill_dir, body.get("deps"))
    venv_py, deps_installed, dep_err = _ensure_venv(cache_base, reqs)
    if dep_err:
        return {"ok": False, "error": dep_err, "runtime": "native-bridge",
                "deps_requested": reqs}

    # ── build the interpreter command for this script type ──
    if ext == ".py":
        interp = str(venv_py) if venv_py else sys.executable
        cmd = [interp, str(script_path)]
    elif ext in (".js", ".mjs"):
        node = shutil.which("node")
        if not node:
            return {"ok": False, "error": "node not found on PATH (needed to run .js/.mjs skills)"}
        cmd = [node, str(script_path)]
    else:  # .sh / .bash
        bash = shutil.which("bash") or "/bin/bash"
        cmd = [bash, str(script_path)]

    # real sys.argv tail
    argv = body.get("argv")
    if isinstance(argv, (list, tuple)):
        cmd += [str(a) for a in argv]

    # real environment (inherit + caller additions). PYTHONNOUSERSITE keeps the
    # venv clean from the user's ~/.local site-packages.
    run_env = dict(os.environ)
    run_env["PYTHONNOUSERSITE"] = "1"
    run_env["TAIGA_BRIDGE"] = "1"
    extra_env = body.get("env")
    if isinstance(extra_env, dict):
        for k, v in extra_env.items():
            run_env[str(k)] = str(v)

    # real stdin (the "input" field — same name the rest of Taiga uses)
    stdin_text = body.get("input")
    stdin_bytes = None if stdin_text is None else str(stdin_text).encode("utf-8")

    # ── snapshot → run natively → snapshot (to detect produced files) ──
    before = _snapshot(skill_dir)
    started = time.monotonic()
    timed_out = False
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(skill_dir),                  # cwd = skill dir → sibling files readable
            input=stdin_bytes,                   # real stdin
            env=run_env,                         # real env
            capture_output=True,
            timeout=RUN_TIMEOUT_SEC,             # wall-clock cap
        )
        exit_code = proc.returncode
        out_bytes = proc.stdout or b""
        err_bytes = proc.stderr or b""
    except subprocess.TimeoutExpired as e:
        timed_out = True
        exit_code = None
        out_bytes = e.stdout or b""
        err_bytes = (e.stderr or b"") + f"\n[bridge] killed: exceeded {RUN_TIMEOUT_SEC}s time limit".encode()
    duration_ms = int((time.monotonic() - started) * 1000)

    after = _snapshot(skill_dir)
    produced = _collect_produced(skill_dir, before, after)

    def _cap(b: bytes) -> tuple[str, bool]:
        truncated = len(b) > OUTPUT_CAP_BYTES
        return b[:OUTPUT_CAP_BYTES].decode("utf-8", "replace"), truncated

    stdout, out_trunc = _cap(out_bytes)
    stderr, err_trunc = _cap(err_bytes)

    result = {
        "ok": (not timed_out) and exit_code == 0,
        "exit": exit_code,
        "timed_out": timed_out,
        "stdout": stdout,
        "stderr": stderr,
        "stdout_truncated": out_trunc,
        "stderr_truncated": err_trunc,
        "files": produced,
        "runtime": "native-bridge",
        "deps_installed": deps_installed,
        "skill_dir": str(skill_dir),
        "duration_ms": duration_ms,
    }
    return result


# ───────────────────────────── HTTP layer ─────────────────────────────

class BridgeHandler(BaseHTTPRequestHandler):
    server_version = f"TaigaSkillBridge/{VERSION}"
    protocol_version = "HTTP/1.1"

    # ── helpers ──
    def _origin_allowed(self) -> str | None:
        origin = self.headers.get("Origin")
        if origin and origin in ALLOWED_ORIGINS:
            return origin
        return None

    def _set_cors(self):
        origin = self._origin_allowed()
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Credentials", "true")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Bridge-Token")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Max-Age", "600")

    def _send_json(self, code: int, payload: dict, close: bool = False):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if close:
            # Force the keep-alive connection shut so any undrained request body
            # can't be misread as the next request line.
            self.close_connection = True
            self.send_header("Connection", "close")
        self._set_cors()
        self.end_headers()
        try:
            self.wfile.write(body)
        except Exception:
            pass

    def _token_ok(self) -> bool:
        sent = self.headers.get("X-Bridge-Token", "")
        # constant-time compare
        return secrets.compare_digest(sent, SESSION_TOKEN)

    # ── verbs ──
    def do_OPTIONS(self):  # noqa: N802 (stdlib naming)
        # CORS preflight — no token needed; just advertise what we allow.
        self.send_response(204)
        self._set_cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):  # noqa: N802
        if self.path.split("?", 1)[0] == "/health":
            # NO token required → the web app can detect the bridge before it has
            # the token entered. Deliberately leaks nothing sensitive.
            self._send_json(200, {
                "ok": True,
                "service": "taiga-skill-bridge",
                "version": VERSION,
                "python": sys.version.split()[0],
                "platform": platform.platform(),
                "token_required": True,
                "endpoints": ["/health", "/run"],
            })
            return
        self._send_json(404, {"ok": False, "error": "not found"})

    def do_POST(self):  # noqa: N802
        path = self.path.split("?", 1)[0]
        # Determine declared body length up front.
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        max_body = SKILL_TOTAL_MAX_BYTES + (4 * 1024 * 1024)

        if path != "/run":
            self._send_json(404, {"ok": False, "error": "not found"}, close=True)
            return

        # ALWAYS drain the request body before answering, so that an early exit
        # (bad token / bad JSON) doesn't leave unread bytes that the next
        # keep-alive request line would choke on. Oversized bodies are rejected
        # without reading the whole thing (and we close the connection).
        if length < 0 or length > max_body:
            self._send_json(400, {"ok": False, "error": "empty or oversized request body"}, close=True)
            return
        try:
            raw = self.rfile.read(length) if length > 0 else b""
        except Exception:
            self.close_connection = True
            return

        # token check (after the body is drained)
        if not self._token_ok():
            self._send_json(401, {"ok": False, "error": "missing or invalid X-Bridge-Token"})
            return
        if not raw:
            self._send_json(400, {"ok": False, "error": "empty request body"})
            return
        try:
            body = json.loads(raw.decode("utf-8"))
        except Exception as e:
            self._send_json(400, {"ok": False, "error": f"invalid JSON body: {e}"})
            return
        if not isinstance(body, dict):
            self._send_json(400, {"ok": False, "error": "body must be a JSON object"})
            return

        # Execute. Catch everything so the daemon never dies on a bad skill.
        try:
            result = run_skill(body)
        except Exception as e:
            self._send_json(500, {"ok": False, "error": f"bridge run error: {e}",
                                  "runtime": "native-bridge"})
            return
        self._send_json(200, result)  # run failures reported in-band (ok:false)

    # quieter logging (one concise line per request)
    def log_message(self, fmt, *args):  # noqa: A003
        sys.stderr.write("[bridge] %s - %s\n" % (self.address_string(), fmt % args))


# ───────────────────────────── startup ─────────────────────────────

_STARTUP_WARNING = """\
============================================================================
 Taiga Skill Bridge  v{ver}   (LOCAL native skill runner)
============================================================================
 SECURITY — READ THIS:
   This daemon executes skill code NATIVELY on THIS machine (real Python,
   pip packages, shell, filesystem). That is arbitrary code execution by
   design — exactly like Claude desktop running a skill.

   Safeguards in place:
     * binds {host} ONLY (never exposed to your network)
     * every /run requires the session token below
     * NOTHING runs automatically — code executes only when the Taiga tab
       you are using sends an explicit /run request
     * CORS locked to: {origins}

   Only run skills you TRUST. Treat an installed skill like a script you
   downloaded and chose to execute.
----------------------------------------------------------------------------
 Listening : http://{host}:{port}
 Health    : http://{host}:{port}/health   (no token — for bridge detection)
 Run       : POST http://{host}:{port}/run (header  X-Bridge-Token: <token>)
 Cache     : {cache}

 SESSION TOKEN (paste into Taiga's "local bridge" settings):

     {token}

 Press Ctrl+C to stop. No background execution happens after you stop.
============================================================================
"""


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Taiga Skill Bridge — local native skill runner")
    ap.add_argument("--port", type=int, default=int(os.environ.get("TAIGA_BRIDGE_PORT", DEFAULT_PORT)))
    args = ap.parse_args()

    CACHE_ROOT.mkdir(parents=True, exist_ok=True)

    origins = ", ".join(sorted(ALLOWED_ORIGINS)) or "(none)"
    sys.stderr.write(_STARTUP_WARNING.format(
        ver=VERSION, host=HOST, port=args.port, token=SESSION_TOKEN,
        origins=origins, cache=str(CACHE_ROOT),
    ))
    sys.stderr.flush()

    httpd = ThreadingHTTPServer((HOST, args.port), BridgeHandler)
    # daemon threads so Ctrl+C exits promptly even mid-request
    httpd.daemon_threads = True
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        sys.stderr.write("\n[bridge] shutting down (Ctrl+C). No background jobs remain.\n")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()

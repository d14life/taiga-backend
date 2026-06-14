"""skill_caps.py — STATIC capability analyzer for Taiga's skill compatibility layer.

Lane A (NEW backend file, see SKILL-TRANSFORMER-PLAN.md). Given an imported skill
folder (SKILL.md + scripts/ + resources/), it READS the files and classifies WHAT the
skill needs, then assigns a compatibility badge. It NEVER executes the skill: no exec,
no eval, no import of the skill, no subprocess — pure read-only token/regex/AST-free
scanning over file text.

It will be wired into ``skills_run.py`` LATER by another agent. A frontend twin
(``taiga-web/src/lib/skills/skill-caps.ts``) mirrors the EXACT caps schema below, so the
key names here are load-bearing — do not rename them.

Public API
----------
- ``detect_skill_caps(skill_dir) -> dict``   the caps dict (exact schema below)
- ``compute_badge(caps) -> str``             "full"|"partial"|"instruction-only"|"needs-server"|"unsupported"
- ``analyze_skill(skill_dir) -> dict``        {**caps, "badge": compute_badge(caps)}

caps schema (keys MUST stay exactly these)::

    {
      "language": "python"|"js"|"bash"|"none",
      "imports": [str],
      "third_party_packages": [str],
      "pyodide_ok": [str],
      "pyodide_no": [str],
      "needs_argv": bool,
      "needs_resources": bool,
      "needs_shell": bool,
      "needs_network": bool,
      "needs_node": bool,
      "media_verbs": [str],
      "claude_authored": bool,
      "recommended_model": str | None,
    }

Pure Python stdlib only (no pip deps).
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# Default Claude model pin for claude-authored skills with no explicit model (matches
# server.py injection convention `ng:claude-opus-4-8`).
DEFAULT_CLAUDE_MODEL = "ng:claude-opus-4-8"

# Media verbs a skill's SKILL.md may name; Taiga maps these to native generation tools.
MEDIA_VERBS = (
    "generate_image",
    "generate_audio",
    "generate_video",
    "generate_music",
    "generate_speech",
)

# Script extensions we scan (same set skills_run.py imports as SCRIPT_EXTS).
_PY_EXTS = (".py",)
_JS_EXTS = (".js", ".mjs")
_SH_EXTS = (".sh", ".bash")
_SCRIPT_EXTS = _PY_EXTS + _JS_EXTS + _SH_EXTS

# Extensions that count as "sibling bundle files" a script might read at runtime
# (used for the needs_resources heuristic when SKILL.md names a bundle file).
_RESOURCE_EXTS = (
    ".md", ".txt", ".json", ".yaml", ".yml", ".csv", ".toml", ".cfg", ".ini",
    ".tsv", ".xml", ".html", ".htm", ".jinja", ".j2", ".tmpl", ".template",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".pdf", ".ico",
    ".woff", ".woff2", ".ttf", ".otf", ".data", ".bin", ".npy", ".npz",
    ".pkl", ".parquet", ".sqlite", ".db", ".wasm",
)

_MAX_FILE_BYTES = 512 * 1024  # mirror skills_run.FILE_MAX_BYTES; don't slurp huge blobs

# ── Node.js builtin modules (so JS imports get a third-party / builtin split too) ──
_NODE_BUILTINS = frozenset({
    "assert", "async_hooks", "buffer", "child_process", "cluster", "console",
    "constants", "crypto", "dgram", "diagnostics_channel", "dns", "domain",
    "events", "fs", "http", "http2", "https", "inspector", "module", "net",
    "os", "path", "perf_hooks", "process", "punycode", "querystring", "readline",
    "repl", "stream", "string_decoder", "sys", "timers", "tls", "trace_events",
    "tty", "url", "util", "v8", "vm", "wasi", "worker_threads", "zlib",
})

# Fallback Python stdlib top-level names (used only if sys.stdlib_module_names is
# unavailable — i.e. < 3.10). Conservative superset of common stdlib packages.
_STDLIB_FALLBACK = frozenset({
    "__future__", "_thread", "abc", "aifc", "argparse", "array", "ast", "asyncio",
    "atexit", "audioop", "base64", "bdb", "binascii", "bisect", "builtins", "bz2",
    "calendar", "cgi", "cgitb", "chunk", "cmath", "cmd", "code", "codecs", "codeop",
    "collections", "colorsys", "compileall", "concurrent", "configparser",
    "contextlib", "contextvars", "copy", "copyreg", "cProfile", "crypt", "csv",
    "ctypes", "curses", "dataclasses", "datetime", "dbm", "decimal", "difflib",
    "dis", "doctest", "email", "encodings", "ensurepip", "enum", "errno",
    "faulthandler", "fcntl", "filecmp", "fileinput", "fnmatch", "fractions",
    "ftplib", "functools", "gc", "getopt", "getpass", "gettext", "glob", "graphlib",
    "grp", "gzip", "hashlib", "heapq", "hmac", "html", "http", "idlelib", "imaplib",
    "imghdr", "imp", "importlib", "inspect", "io", "ipaddress", "itertools", "json",
    "keyword", "lib2to3", "linecache", "locale", "logging", "lzma", "mailbox",
    "mailcap", "marshal", "math", "mimetypes", "mmap", "modulefinder", "msilib",
    "msvcrt", "multiprocessing", "netrc", "nis", "nntplib", "numbers", "operator",
    "optparse", "os", "ossaudiodev", "pathlib", "pdb", "pickle", "pickletools",
    "pipes", "pkgutil", "platform", "plistlib", "poplib", "posix", "pprint",
    "profile", "pstats", "pty", "pwd", "py_compile", "pyclbr", "pydoc", "queue",
    "quopri", "random", "re", "readline", "reprlib", "resource", "rlcompleter",
    "runpy", "sched", "secrets", "select", "selectors", "shelve", "shlex", "shutil",
    "signal", "site", "smtpd", "smtplib", "sndhdr", "socket", "socketserver",
    "spwd", "sqlite3", "ssl", "stat", "statistics", "string", "stringprep",
    "struct", "subprocess", "sunau", "symtable", "sys", "sysconfig", "syslog",
    "tabnanny", "tarfile", "telnetlib", "tempfile", "termios", "test", "textwrap",
    "threading", "time", "timeit", "tkinter", "token", "tokenize", "tomllib",
    "trace", "traceback", "tracemalloc", "tty", "turtle", "turtledemo", "types",
    "typing", "unicodedata", "unittest", "urllib", "uu", "uuid", "venv", "warnings",
    "wave", "weakref", "webbrowser", "winreg", "winsound", "wsgiref", "xdrlib",
    "xml", "xmlrpc", "zipapp", "zipfile", "zipimport", "zlib", "zoneinfo",
})


# ────────────────────────────── small helpers ──────────────────────────────

def _stdlib_names() -> frozenset:
    """Top-level Python stdlib module names. Prefer sys.stdlib_module_names (3.10+)."""
    names = getattr(sys, "stdlib_module_names", None)
    if names:
        return frozenset(names)
    return _STDLIB_FALLBACK


def _load_pyodide_packages():
    """Load the Pyodide allowlist (bundled+micropip) sitting beside this module.

    Returns a lowercased set of acceptable package/import names. On any failure
    (missing/corrupt file) returns an empty set — analyzer still works, every
    third-party import just lands in pyodide_no (conservative, fail-closed)."""
    here = Path(__file__).resolve().parent
    fp = here / "skill_pyodide_packages.json"
    try:
        data = json.loads(fp.read_text("utf-8"))
    except Exception:
        return set()
    ok = set()
    for key in ("bundled", "micropip"):
        for name in data.get(key, []) or []:
            if isinstance(name, str) and name.strip():
                ok.add(_norm_pkg(name))
    return ok


def _norm_pkg(name: str) -> str:
    """Normalize a package/import token to a comparable key: lowercased, top-level,
    PyPI dashes/underscores unified to '-'? No — we keep BOTH forms reachable by
    lowercasing only and letting the allowlist carry both spellings. Strip subpaths."""
    n = str(name or "").strip().lower()
    # top-level only (foo.bar -> foo ; foo/bar -> foo)
    n = re.split(r"[./\\]", n, maxsplit=1)[0]
    return n


def _top_level(mod: str) -> str:
    """Top-level package of a dotted import path: 'foo.bar.baz' -> 'foo'."""
    return (mod or "").split(".", 1)[0].strip()


def _read_text(p: Path) -> str:
    try:
        if p.stat().st_size > _MAX_FILE_BYTES:
            return ""
        return p.read_text("utf-8", "ignore")
    except Exception:
        return ""


def _uniq_sorted(seq):
    return sorted({s for s in seq if s})


# ────────────────────────────── file discovery ──────────────────────────────

def _walk_files(root: Path):
    """Yield (path, rel_lower_name) for every regular file under root (recursive)."""
    for dirpath, dirnames, filenames in os.walk(root):
        # skip junk / vendored dirs that never carry skill logic
        dirnames[:] = [d for d in dirnames if d not in (
            "__pycache__", ".git", "node_modules", ".venv", "venv", ".mypy_cache",
        )]
        for fn in filenames:
            yield Path(dirpath) / fn


def _find_skill_md(root: Path):
    """The skill's SKILL.md (topmost if several). Returns (Path|None)."""
    candidates = [p for p in _walk_files(root) if p.name.lower() == "skill.md"]
    if not candidates:
        return None
    # topmost = fewest path parts relative to root, tie-break by string
    candidates.sort(key=lambda p: (len(p.relative_to(root).parts), str(p).lower()))
    return candidates[0]


# ────────────────────────────── import extraction ──────────────────────────────

# Python: lines like `import a.b, c` or `from a.b import x`. Capture the module path.
_PY_IMPORT_RE = re.compile(
    r"^\s*(?:import|from)\s+([a-zA-Z0-9_][a-zA-Z0-9_\.]*)", re.MULTILINE
)
# Also catch the rest of a multi-name `import a, b, c` line for the import (not from) form.
_PY_IMPORT_LINE_RE = re.compile(r"^\s*import\s+(.+)$", re.MULTILINE)

# JS/TS: require('x') / require("x") and  import ... from 'x' / import 'x'
_JS_REQUIRE_RE = re.compile(r"""require\(\s*['"]([^'"]+)['"]\s*\)""")
_JS_IMPORT_FROM_RE = re.compile(r"""\bfrom\s+['"]([^'"]+)['"]""")
_JS_IMPORT_BARE_RE = re.compile(r"""^\s*import\s+['"]([^'"]+)['"]""", re.MULTILINE)
_JS_DYN_IMPORT_RE = re.compile(r"""\bimport\(\s*['"]([^'"]+)['"]\s*\)""")


def _py_imports(text: str):
    """All top-level imported package names from one .py file's text."""
    out = set()
    for m in _PY_IMPORT_RE.finditer(text):
        tl = _top_level(m.group(1))
        if tl:
            out.add(tl)
    # handle `import a, b as c, d` extra names on the line
    for m in _PY_IMPORT_LINE_RE.finditer(text):
        for chunk in m.group(1).split(","):
            name = chunk.strip().split(" as ", 1)[0].strip()
            tl = _top_level(name)
            if tl and re.match(r"^[a-zA-Z0-9_\.]+$", name or ""):
                out.add(tl)
    out.discard("")
    return out


def _js_imports(text: str):
    """All top-level required/imported package names from one .js/.mjs file's text.
    Strips relative paths ('./x', '../x') and scoped/subpath specifiers."""
    raw = set()
    for rx in (_JS_REQUIRE_RE, _JS_IMPORT_FROM_RE, _JS_IMPORT_BARE_RE, _JS_DYN_IMPORT_RE):
        for m in rx.finditer(text):
            raw.add(m.group(1))
    out = set()
    for spec in raw:
        spec = spec.strip()
        if not spec or spec.startswith(".") or spec.startswith("/"):
            continue  # relative / absolute file import — not a package
        if spec.startswith("node:"):
            spec = spec[len("node:"):]
        if spec.startswith("@"):
            # scoped: @scope/name/sub -> @scope/name
            parts = spec.split("/")
            top = "/".join(parts[:2]) if len(parts) >= 2 else spec
        else:
            top = spec.split("/", 1)[0]
        if top:
            out.add(top)
    return out


# ────────────────────────────── token scans ──────────────────────────────

# argv / CLI usage
_ARGV_RE = re.compile(
    r"\bsys\.argv\b|\bargparse\b|\bgetopt\b|\bfrom\s+argparse\b|\bimport\s+click\b"
    r"|\bfrom\s+click\b|@click\.|\bclick\.command\b|\bclick\.option\b"
    r"|__name__\s*==\s*['\"]__main__['\"]|\bprocess\.argv\b|\bArgumentParser\b"
)

# subprocess / shell / external binaries
_SHELL_RE = re.compile(
    r"\bsubprocess\b|\bos\.system\b|\bos\.popen\b|\bos\.exec[lv]p?e?\b|\bpty\.spawn\b"
    r"|\bcommands\.getoutput\b|\bsh\.[a-zA-Z_]|\bplumbum\b"
    r"|\bchild_process\b|\bexeca\b|\bexecSync\b|\bspawnSync\b|\bshelljs\b"
    r"|\b(?:git|curl|wget|ffmpeg|ffprobe|imagemagick|convert|magick|pandoc|"
    r"docker|bash|sh|npm|npx|node|pip|brew|apt|yum|make|gcc|rsync|ssh|scp)\b"
)
# the bare-binary token half of _SHELL_RE should only count inside shell scripts or
# when an exec primitive is present — see _scan_shell for the gating.
_EXEC_PRIMITIVE_RE = re.compile(
    r"\bsubprocess\b|\bos\.system\b|\bos\.popen\b|\bos\.exec[lv]p?e?\b|\bpty\.spawn\b"
    r"|\bcommands\.getoutput\b|\bplumbum\b|\bchild_process\b|\bexeca\b"
    r"|\bexecSync\b|\bspawnSync\b|\bshelljs\b|\bos\.spawn"
)
_BINARY_TOKEN_RE = re.compile(
    r"\b(?:git|curl|wget|ffmpeg|ffprobe|imagemagick|magick|pandoc|docker|"
    r"rsync|ssh|scp|youtube-dl|yt-dlp|tesseract|libreoffice|soffice)\b"
)

# network
_NET_RE = re.compile(
    r"\bimport\s+socket\b|\bfrom\s+socket\b|\bsocket\.socket\b|\burllib\b|\burllib2\b"
    r"|\brequests\b|\bhttpx\b|\baiohttp\b|\bhttp\.client\b|\bfrom\s+http\b"
    r"|\bhttplib\b|\bwebsocket\b|\bwebsockets\b|\bxmlrpc\b|\bftplib\b|\bsmtplib\b"
    r"|\bpoplib\b|\bimaplib\b|\btelnetlib\b|\burlopen\b|\bfetch\(|\baxios\b"
    r"|\bnode-fetch\b|\bgot\b\s*=|https?://"
)


def _scan_argv(texts) -> bool:
    return any(_ARGV_RE.search(t) for t in texts)


def _scan_shell(py_js_texts, sh_texts) -> bool:
    """needs_shell if: any .sh/.bash script present with content, OR a Python/JS
    exec primitive (subprocess/os.system/child_process...), OR a real external
    binary token (git/curl/ffmpeg...) appears together with an exec primitive or
    inside a shell script."""
    if any(t.strip() for t in sh_texts):
        return True
    for t in py_js_texts:
        if _EXEC_PRIMITIVE_RE.search(t):
            return True
    # a bare binary token alone in a py/js file is weak signal; require exec primitive
    # (already checked) — so do not flag on _BINARY_TOKEN_RE in py/js without a primitive.
    return False


def _scan_network(texts) -> bool:
    return any(_NET_RE.search(t) for t in texts)


def _scan_resources(py_js_texts, skill_md_text, bundle_names) -> bool:
    """needs_resources if a script reads sibling files, OR SKILL.md names a sibling
    bundle file. Signals:
      - open(...) / Path(...) / __file__ / pathlib usage with a relative path
      - reads from references/ resources/ assets/ data/ scripts/ subfolders
      - SKILL.md text mentions any actual sibling bundle filename."""
    read_re = re.compile(
        r"\bopen\s*\(|__file__|\bPath\s*\(|\bpathlib\b|\bos\.path\.(?:join|dirname)\b"
        r"|\b__dir__\b|\bimportlib\.resources\b|\bpkgutil\.get_data\b"
        r"|\breadFileSync\b|\bfs\.read|\b__dirname\b|\brequire\.resolve\b"
        r"|\bloadtxt\b|\bread_csv\b|\bread_json\b|\bread_excel\b"
    )
    folder_re = re.compile(
        r"['\"](?:\./)?(?:references|resources|assets|data|scripts|templates|"
        r"reference|examples?|fixtures?|prompts?|schemas?)/", re.IGNORECASE
    )
    for t in py_js_texts:
        if read_re.search(t) or folder_re.search(t):
            return True
    # SKILL.md referencing an actual sibling bundle filename
    if skill_md_text and bundle_names:
        low = skill_md_text.lower()
        for name in bundle_names:
            nl = name.lower()
            if not nl or nl == "skill.md":
                continue
            # mention of the basename or a path containing it
            if nl in low:
                return True
    return False


def _scan_media_verbs(skill_md_text) -> list:
    low = (skill_md_text or "").lower()
    return [v for v in MEDIA_VERBS if v in low]


def _frontmatter(skill_md_text: str):
    """Return (frontmatter_block_str or '', body_str). Simple --- ... --- at top."""
    if not skill_md_text:
        return "", ""
    m = re.match(r"^\s*---\s*\n(.*?)\n---\s*\n?(.*)$", skill_md_text, re.S)
    if m:
        return m.group(1), m.group(2)
    return "", skill_md_text


def _fm_value(fm: str, *keys):
    """Extract a simple top-level scalar value for the first matching key in the
    YAML frontmatter block. Handles `key: value`, quoted values; ignores block
    scalars (returns '' for `key: |`). keys are matched case-insensitively."""
    if not fm:
        return ""
    wanted = {k.lower() for k in keys}
    for line in fm.splitlines():
        if ":" not in line:
            continue
        # only top-level keys (no leading indentation) to avoid nested metadata
        if line[:1] in (" ", "\t"):
            continue
        k, v = line.split(":", 1)
        if k.strip().lower() in wanted:
            val = v.strip().strip('"').strip("'").strip()
            if val in ("|", ">", "|-", ">-", "|+", ">+"):
                return ""  # block scalar, not a simple model id
            return val
    return ""


_CLAUDE_HINT_RE = re.compile(
    r"\banthropic\b|\bclaude[\s\-_]?(?:code|opus|sonnet|haiku|3|4|model)?\b"
    r"|\bclaude\.ai\b|github\.com/anthropics?\b|model:\s*claude",
    re.IGNORECASE,
)


def _detect_claude(skill_md_text, fm, source_url, model_val) -> bool:
    """claude_authored if the model id is a claude id, OR frontmatter/source host
    mentions anthropic/claude, OR SKILL.md body clearly references Claude/Anthropic."""
    if model_val and re.search(r"claude|anthropic", model_val, re.IGNORECASE):
        return True
    for blob in (source_url or "", fm or ""):
        if re.search(r"anthropic|claude\.ai|github\.com/anthropics?", blob, re.IGNORECASE):
            return True
    # frontmatter author/website fields naming anthropic
    if fm and re.search(r"(?:author|website|by|org)\s*:.*(?:anthropic|claude)", fm, re.IGNORECASE):
        return True
    # body mention (kept fairly specific to avoid every skill that says "claude" once)
    if skill_md_text and _CLAUDE_HINT_RE.search(skill_md_text):
        # require an anthropic/claude.ai/github-anthropics signal OR an explicit
        # "model: claude" / "by claude" / "authored ... claude" phrasing to reduce noise
        strong = re.search(
            r"anthropic|claude\.ai|github\.com/anthropics?|model:\s*claude"
            r"|authored\s+by\s+claude|by\s+claude\b|created\s+by\s+claude",
            skill_md_text, re.IGNORECASE,
        )
        if strong:
            return True
    return False


# ────────────────────────────── primary language ──────────────────────────────

def _primary_language(script_paths) -> str:
    """python > js > bash by presence; 'none' if no scripts. Python wins ties because
    it is the runnable-in-browser path Taiga optimizes for."""
    exts = {p.suffix.lower() for p in script_paths}
    if any(e in _PY_EXTS for e in exts):
        return "python"
    if any(e in _JS_EXTS for e in exts):
        return "js"
    if any(e in _SH_EXTS for e in exts):
        return "bash"
    return "none"


# ────────────────────────────── public: detect ──────────────────────────────

def detect_skill_caps(skill_dir: str) -> dict:
    """Statically analyze a skill folder and return the caps dict (exact schema).

    Read-only: opens and scans text files; never executes the skill. Robust to a
    missing/empty dir (returns an all-empty caps with language 'none')."""
    root = Path(skill_dir)
    caps = {
        "language": "none",
        "imports": [],
        "third_party_packages": [],
        "pyodide_ok": [],
        "pyodide_no": [],
        "needs_argv": False,
        "needs_resources": False,
        "needs_shell": False,
        "needs_network": False,
        "needs_node": False,
        "media_verbs": [],
        "claude_authored": False,
        "recommended_model": None,
    }
    if not root.exists() or not root.is_dir():
        return caps

    all_files = list(_walk_files(root))
    script_paths = [p for p in all_files if p.suffix.lower() in _SCRIPT_EXTS]
    py_paths = [p for p in script_paths if p.suffix.lower() in _PY_EXTS]
    js_paths = [p for p in script_paths if p.suffix.lower() in _JS_EXTS]
    sh_paths = [p for p in script_paths if p.suffix.lower() in _SH_EXTS]

    # SKILL.md
    skill_md_path = _find_skill_md(root)
    skill_md_text = _read_text(skill_md_path) if skill_md_path else ""

    # bundle filenames = all sibling resource files (for needs_resources via SKILL.md)
    bundle_names = [
        p.name for p in all_files
        if p.suffix.lower() in _RESOURCE_EXTS and p.name.lower() != "skill.md"
    ]

    # ── language ──
    caps["language"] = _primary_language(script_paths)

    # ── imports + third-party split ──
    py_texts = [_read_text(p) for p in py_paths]
    js_texts = [_read_text(p) for p in js_paths]
    sh_texts = [_read_text(p) for p in sh_paths]

    py_imports = set()
    for t in py_texts:
        py_imports |= _py_imports(t)
    js_imports = set()
    for t in js_texts:
        js_imports |= _js_imports(t)

    caps["imports"] = _uniq_sorted(py_imports | js_imports)

    stdlib = _stdlib_names()
    pyo_allow = _load_pyodide_packages()

    # third-party = imports not in the relevant builtin set. Python imports judged
    # against the Python stdlib; JS imports judged against Node builtins.
    third_party = set()
    py_third = set()
    for name in py_imports:
        if name and name not in stdlib and not name.startswith("_"):
            third_party.add(name)
            py_third.add(name)
    for name in js_imports:
        # node builtins (and node:-prefixed) are not "third party"
        bare = name[len("node:"):] if name.startswith("node:") else name
        if name and bare not in _NODE_BUILTINS:
            third_party.add(name)
    caps["third_party_packages"] = _uniq_sorted(third_party)

    # ── pyodide split (Python third-party only) ──
    ok, no = [], []
    for name in py_third:
        if _norm_pkg(name) in pyo_allow:
            ok.append(name)
        else:
            no.append(name)
    caps["pyodide_ok"] = _uniq_sorted(ok)
    caps["pyodide_no"] = _uniq_sorted(no)

    # ── boolean capability scans ──
    code_texts = py_texts + js_texts + sh_texts
    py_js_texts = py_texts + js_texts

    caps["needs_argv"] = _scan_argv(code_texts)
    caps["needs_shell"] = _scan_shell(py_js_texts, sh_texts)
    caps["needs_network"] = _scan_network(code_texts)
    caps["needs_resources"] = _scan_resources(py_js_texts, skill_md_text, bundle_names)

    # needs_node: a .js/.mjs script that uses require/import/process/fs (i.e. real
    # Node program, not just an empty file).
    node_use_re = re.compile(
        r"\brequire\s*\(|\bimport\s+|\bexport\s+|\bprocess\.|\b__dirname\b|\bmodule\.exports\b"
        r"|\bfrom\s+['\"]|\bfs\.|\bBuffer\b"
    )
    caps["needs_node"] = bool(js_paths) and any(node_use_re.search(t) for t in js_texts)

    # ── media verbs ──
    caps["media_verbs"] = _scan_media_verbs(skill_md_text)

    # ── claude authorship + recommended model ──
    fm, _body = _frontmatter(skill_md_text)
    model_val = _fm_value(fm, "model", "recommended-model", "recommended_model")
    source_url = ""  # standalone analyzer has no host; reserved for caller-supplied meta
    caps["claude_authored"] = _detect_claude(skill_md_text, fm, source_url, model_val)

    if model_val:
        caps["recommended_model"] = model_val
    elif caps["claude_authored"]:
        caps["recommended_model"] = DEFAULT_CLAUDE_MODEL
    else:
        caps["recommended_model"] = None

    return caps


# ────────────────────────────── public: badge ──────────────────────────────

def compute_badge(caps: dict) -> str:
    """Map a caps dict to one of:
        "full" | "partial" | "instruction-only" | "needs-server" | "unsupported"

    Precedence (FIRST match wins), tuned so a REAL server need (shell/network/node/
    non-Pyodide package) always outranks the soft "instruction-only" fallback:

      1. full           — runs natively & losslessly in Taiga.
      2. needs-server   — hard server requirement (shell / network / node /
                          non-Pyodide package). Checked BEFORE partial/instruction
                          so these never get mislabeled as merely lossy.
      3. partial        — runnable but lossy (owner-recoverable argv/resources, OR
                          Pyodide packages that load slowly, OR claude prose with no
                          model pin).
      4. instruction-only — has scripts that can't run locally but no hard server
                          need (text/SKILL.md still useful as instructions).
      5. unsupported    — empty / broken / nothing classifiable.
    """
    if not isinstance(caps, dict):
        return "unsupported"

    language = caps.get("language", "none")
    media_verbs = caps.get("media_verbs") or []
    pyodide_ok = caps.get("pyodide_ok") or []
    pyodide_no = caps.get("pyodide_no") or []
    third_party = caps.get("third_party_packages") or []
    needs_argv = bool(caps.get("needs_argv"))
    needs_resources = bool(caps.get("needs_resources"))
    needs_shell = bool(caps.get("needs_shell"))
    needs_network = bool(caps.get("needs_network"))
    needs_node = bool(caps.get("needs_node"))
    claude_authored = bool(caps.get("claude_authored"))
    recommended_model = caps.get("recommended_model")

    hard_server = needs_shell or needs_network or needs_node or bool(pyodide_no)

    # 1) full
    if language == "none":
        # prose / instruction skill with no scripts. Media verbs map natively to
        # Taiga generation tools, so a prose skill that only needs media is still full.
        if not hard_server:
            # a claude-authored prose skill with NO model pin is "partial" (wants a
            # model pin for native quality) — handled at step 3; here require either
            # not-claude OR a model already chosen.
            if not (claude_authored and not recommended_model):
                return "full"
    elif language == "python":
        if (not pyodide_no and not needs_argv and not needs_resources
                and not needs_shell and not needs_network):
            # pure stdlib OR only-pyodide_ok with no argv/resources/shell/net.
            # (pyodide_ok non-empty still loads in-browser; it's lossless-runnable,
            #  but per the plan we treat slow-load as 'partial' — so require empty
            #  pyodide_ok here for the clean 'full'.)
            if not pyodide_ok:
                return "full"

    # 2) needs-server (hard requirement) — outrank partial/instruction-only.
    if hard_server:
        return "needs-server"

    # 3) partial — runnable but lossy.
    if needs_argv or needs_resources:
        return "partial"
    if pyodide_ok:
        return "partial"
    if language == "none" and claude_authored and not recommended_model:
        return "partial"

    # 4) instruction-only — scripts exist but can't run locally, no hard server need.
    if language in ("python", "js", "bash") and (third_party or language == "bash"):
        return "instruction-only"
    if language in ("js", "bash"):
        return "instruction-only"

    # 5) unsupported — nothing else applied (e.g. empty/broken skill, or a python
    # script that somehow fell through). A python script with no blockers already
    # returned 'full' at step 1; reaching here means no usable classification.
    if language == "none":
        # prose skill that wasn't 'full' and isn't claude-partial → still instruction-like
        return "instruction-only"
    return "unsupported"


# ────────────────────────────── public: analyze ──────────────────────────────

def analyze_skill(skill_dir: str) -> dict:
    """Convenience: full caps + computed badge in one dict."""
    caps = detect_skill_caps(skill_dir)
    return {**caps, "badge": compute_badge(caps)}


# ────────────────────────────── self-test ──────────────────────────────

def _selftest():
    """Build three tiny temp skills and print analyze_skill() for each.

    Expectations (per task):
      (a) pure-stdlib python script        -> full
      (b) numpy + argparse + open(refs/x)  -> partial OR needs-server
      (c) SKILL.md-only prose skill        -> full
    Cleans up its temp dir afterwards."""
    import tempfile
    import shutil

    base = Path(tempfile.mkdtemp(prefix="skillcaps_selftest_"))
    results = {}
    try:
        # (a) pure stdlib python
        a = base / "a_stdlib"
        (a / "scripts").mkdir(parents=True)
        (a / "SKILL.md").write_text(
            "---\nname: stdlib-tool\ndescription: counts words\n---\n# Stdlib tool\n",
            "utf-8",
        )
        (a / "scripts" / "run.py").write_text(
            "import json, re, collections\n"
            "def main():\n"
            "    text = 'hello hello world'\n"
            "    c = collections.Counter(re.findall(r'\\w+', text))\n"
            "    print(json.dumps(dict(c)))\n"
            "main()\n",
            "utf-8",
        )

        # (b) numpy + argparse + reads sibling resource file
        b = base / "b_numpy_cli"
        (b / "scripts").mkdir(parents=True)
        (b / "references").mkdir(parents=True)
        (b / "references" / "x.md").write_text("ref data\n", "utf-8")
        (b / "SKILL.md").write_text(
            "---\nname: numpy-cli\ndescription: matrix stats\n---\n"
            "# Numpy CLI\nUses references/x.md for config.\n",
            "utf-8",
        )
        (b / "scripts" / "tool.py").write_text(
            "import argparse, numpy as np\n"
            "def main():\n"
            "    ap = argparse.ArgumentParser()\n"
            "    ap.add_argument('--n', type=int, default=3)\n"
            "    args = ap.parse_args()\n"
            "    data = open('references/x.md').read()\n"
            "    print(np.arange(args.n).sum(), len(data))\n"
            "if __name__ == '__main__':\n"
            "    main()\n",
            "utf-8",
        )

        # (c) prose-only skill (no scripts)
        c = base / "c_prose"
        c.mkdir(parents=True)
        (c / "SKILL.md").write_text(
            "---\nname: writing-coach\ndescription: improve prose clarity\n---\n"
            "# Writing coach\nApply these editing principles to any text the user gives.\n"
            "Prefer short sentences. Cut filler. Keep the author's voice.\n",
            "utf-8",
        )

        for label, d in (("a", a), ("b", b), ("c", c)):
            results[label] = analyze_skill(str(d))
    finally:
        shutil.rmtree(base, ignore_errors=True)
    return results


if __name__ == "__main__":
    res = _selftest()
    print("skill_caps.py self-test\n" + "=" * 40)
    expect = {"a": "full", "b": "partial|needs-server", "c": "full"}
    for label in ("a", "b", "c"):
        r = res[label]
        print(f"\nskill ({label}): badge = {r['badge']}   (expected {expect[label]})")
        print(json.dumps(r, ensure_ascii=False, indent=2))
    ok_a = res["a"]["badge"] == "full"
    ok_b = res["b"]["badge"] in ("partial", "needs-server")
    ok_c = res["c"]["badge"] == "full"
    print("\n" + "=" * 40)
    print(f"PASS a(full)={ok_a}  b(partial|needs-server)={ok_b}  c(full)={ok_c}")
    print("SELFTEST", "OK" if (ok_a and ok_b and ok_c) else "FAIL")

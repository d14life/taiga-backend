# Taiga Skill Bridge

A **local, native skill-runner daemon** that lets the Taiga web app execute
installed skills with **full native fidelity** on the user's own machine —
exactly the way Claude desktop runs skills.

It runs a skill's **real** script with real Python, real pip packages, real
`sys.argv`, sibling resource files, real stdin, the real filesystem, and
(optionally) a shell. This is the "native app" path: when the bridge is running,
Taiga skills behave like desktop skills instead of being constrained by the
browser sandbox.

---

## Why this exists — the fidelity gap it closes

Taiga's built-in web skill execution is deliberately limited (anti-RCE on the
shared backend). Two paths exist today, both lossy:

| Capability                     | Browser-WASM (Pyodide) | Owner-server `python -I -c <code>` | **This bridge** |
| ------------------------------ | :--------------------: | :--------------------------------: | :-------------: |
| Arbitrary **pip packages**     |   No (bundled-only)    |               No                   |    **Yes** (per-skill venv) |
| Real **`sys.argv`**            |          No            |               No                   |    **Yes** |
| **Sibling resource files**     |   No (no real FS)      |     No (empty tempdir, no cwd)     |    **Yes** (cwd = skill dir) |
| Real **stdin**                 |   Emulated only        |       No (closed stdin)            |    **Yes** |
| **Shell** / external binaries  |          No            |               No                   |    **Yes** (`.sh`/`.bash`, `subprocess`) |
| Real **filesystem** + outputs  |          No            |               No                   |    **Yes** (produced files returned) |

The Taiga web app **detects** the bridge on localhost (`GET /health`) and
**routes** native skills to it (`POST /run` with the session token). When the
bridge is not running, the web app falls back to WASM / cloud-sandbox as before.

---

## How to start

```bash
python3 bridge.py
# optional: choose a port (default 8787)
python3 bridge.py --port 8787
```

Pure Python 3 **stdlib** — no install step, no pip dependencies for the daemon
itself. (It *runs* skills that may pip-install into their own venv.)

On startup it prints a security banner and a fresh **session token**. Paste that
token into Taiga's "local bridge" settings; the web app sends it as the
`X-Bridge-Token` header on every `/run`.

### Environment knobs (all optional)
- `TAIGA_BRIDGE_PORT` — port (default `8787`; `--port` overrides).
- `TAIGA_BRIDGE_TOKEN` — pin a stable token across restarts (default: random per start).
- `TAIGA_BRIDGE_ORIGIN` — additional allowed CORS origin (your Taiga **prod** URL).
- `TAIGA_BRIDGE_CACHE` — where materialized skills + venvs are cached (default: a `taiga-bridge-cache` dir under the system temp dir).

---

## Security & consent model

Running a skill's bundled script natively **is** arbitrary code execution — that
is the entire point (same as Claude desktop running a skill). The bridge makes
that explicit and keeps it as safe as a local tool can:

- **Localhost only.** Binds `127.0.0.1`, never `0.0.0.0`. It is not reachable
  from your network.
- **Token-gated.** A fresh random token is printed on startup. Every endpoint
  **except `/health`** requires `X-Bridge-Token` to equal it (constant-time
  compare). `/health` is intentionally token-free so the web app can *detect*
  the bridge, and it leaks nothing sensitive.
- **No auto-run.** Code executes **only** in response to an explicit `POST /run`
  that the Taiga tab makes on your behalf. There is **no** background worker, no
  scheduler, no cron, no watch — stop the process and nothing of yours keeps
  running.
- **CORS-locked.** Only `http://localhost:3000` (+ `http://127.0.0.1:3000`) and
  one configurable prod origin may call it from a browser, with credentials;
  `OPTIONS` preflight is handled.
- **Bounded.** Per-run wall-clock limit (~120 s), capped stdout/stderr, capped
  number/size of returned files, path-traversal-safe materialization.
- **Trust = consent.** Treat an installed skill like a script you downloaded and
  chose to run. **Only run skills you trust.** A reasonable consent policy for
  the Taiga UI: keep an explicit per-skill allowlist (or a one-time "run natively
  on this machine?" confirmation) before the first `/run` of a given skill. The
  bridge itself never decides to run anything on its own.

---

## Protocol

### `GET /health` — bridge detection (no token)
```json
{
  "ok": true,
  "service": "taiga-skill-bridge",
  "version": "0.1.0",
  "python": "3.13.9",
  "platform": "macOS-...",
  "token_required": true,
  "endpoints": ["/health", "/run"]
}
```

### `POST /run` — native execution (token required)
Header: `X-Bridge-Token: <token>`

Request body:
```jsonc
{
  "skill": {
    "name": "bridge-fidelity-demo",
    "files": {                         // relpath -> content (preserves structure)
      "SKILL.md": "...",
      "scripts/transform.py": "...",
      "resources/data.txt": "...",
      "requirements.txt": "requests\n"
    }
    // ── OR ── point at an existing on-disk skill folder instead of inlining:
    // "skill_dir": "/abs/path/to/skill"
  },
  "script": "scripts/transform.py",    // relative path within the skill dir
  "input":  "stdin text here",         // optional → real process stdin
  "argv":   ["ARG1", "ARG2"],          // optional → real sys.argv[1:]
  "env":    { "KEY": "VALUE" },        // optional → added to the real environment
  "deps":   ["requests==2.32.3"]       // optional → extra pip deps (on top of requirements.txt)
}
```
- Binary input files may be passed as `"relpath": { "b64": "<base64>" }`.

Response body:
```jsonc
{
  "ok": true,
  "exit": 0,
  "timed_out": false,
  "stdout": "...combined output...",
  "stderr": "",
  "files": [                           // files the script created/modified
    { "path": "out/result.json", "text": "..." },
    { "path": "out/thumb.png",  "b64": "..." }   // binary → base64
  ],
  "runtime": "native-bridge",
  "deps_installed": ["requests"],      // what the per-skill venv installed
  "skill_dir": "/.../taiga-bridge-cache/skills/bridge-fidelity-demo/src",
  "duration_ms": 1234
}
```
Run failures are reported **in-band** with HTTP 200 and `"ok": false` (plus
`exit`, `stderr`, or `error`). Auth failures are HTTP 401; bad requests, 400.

### Dependencies / venv
If the skill has a `requirements.txt` (or the request declares `deps`), the
bridge creates a **per-skill venv**, `pip install`s the requirements, and runs
the script with that venv's Python. The venv is **reused** across runs: a
manifest of installed requirements sits beside it, so unchanged requirements skip
pip entirely (fast). Change the requirements and the bridge reinstalls.

---

## How the Taiga web app routes to the bridge

1. On load (or when the user enables "local bridge"), the web app probes
   `GET http://127.0.0.1:8787/health`. If it answers `{ ok: true }`, the bridge
   is available.
2. For a skill the static analyzer classifies as **needing native fidelity**
   (badge `needs-server` / `partial` — i.e. it uses pip packages, argv, sibling
   resources, shell, or network; see `skill_caps.analyze_skill`), the web app
   POSTs the skill's files + chosen script + `input`/`argv` to
   `POST /run` with `X-Bridge-Token`.
3. It renders `stdout`/`stderr`/`files` from the native result instead of the
   WASM result. If `/health` did not answer, it falls back to the existing
   Pyodide / cloud-sandbox paths unchanged.

(The web wiring lives in `taiga-web/src/lib/skills/full-skills.ts`; this bridge
keeps its `/run` payload shape close to that client — same `input` field name,
same `runtime` marker convention — so routing is a thin add.)

---

## Files in this folder

- `bridge.py` — the localhost daemon (stdlib only).
- `sample-skill/` — a tiny skill proving the point:
  - `scripts/transform.py` — uses `sys.argv[1]` + `resources/data.txt` (sibling) + stdin.
  - `scripts/deps_demo.py` — imports the `requests` pip package (per-skill venv).
  - `resources/data.txt` — the sibling resource `transform.py` reads.
  - `requirements.txt` — declares `requests` for the venv path.
  - `SKILL.md` — the skill manifest.

# Тайга ИИ — endpoint smoke-test suite

Stdlib-only (`unittest` + `urllib`, **no pip deps**) smoke tests that run against the
**live** backend (`server.py` on port 8777). They check real HTTP status codes, JSON
keys, and SSE event ordering against the actual endpoint shapes in `server.py` — not
trivially-true assertions.

## How to run

Start the backend first (it must be listening on the port in `TAIGA_BASE`), then from
the **repo root**:

```bash
python3 -m unittest tests.test_endpoints -v
```

Or run the file directly:

```bash
python3 tests/test_endpoints.py
```

Optional helper:

```bash
tests/run.sh            # = python3 -m unittest tests.test_endpoints -v (from repo root)
```

Model calls are slow, so a full run takes ~1–2 minutes. That is expected.

## Env vars

| Var           | Default                  | Meaning                                                        |
|---------------|--------------------------|----------------------------------------------------------------|
| `TAIGA_BASE`  | `http://127.0.0.1:8777`  | Backend base URL.                                              |
| `TAIGA_OWNER` | `default`                | Owner user id (user `default` is the owner per `is_owner`).   |
| `TAIGA_SLOW`  | `120`                    | Per-request timeout (seconds) for endpoints that call models. |

Example against a remote / alternate port:

```bash
TAIGA_BASE=http://127.0.0.1:9000 TAIGA_SLOW=180 python3 -m unittest tests.test_endpoints -v
```

## Robustness (skip, don't fail)

The suite is meant for real founder-grade testing, so it stays green when the *backend
itself* is fine but a *provider* is dry:

- **Backend unreachable** → every test class is **skipped** with a clear message (not failed).
- **Model/provider has no key or no balance** → that single test is **skipped**, detected via
  the SSE `{"type":"error", "message": …}` event or a JSON `402`/`error` body
  (markers like «баланс», «недостаточно», «нет ключа», «не ответили»…).
- **Structural assertions** (status codes, JSON shape, SSE event *types* emitted *before*
  any provider call, owner-gates, input-validation) are always asserted hard — they do not
  depend on provider balance.

## What each test covers

### `TestInit`
- **test_init_200_and_keys** — `GET /api/init` → `200`, JSON contains
  `users, models, full, system, keys, balance, balances, billing, byok, settings, memory`;
  `models` is a list, `billing` is an object, and `billing.owner is True` for the owner.

### `TestChat`
- **test_chat_sse_meta_delta_done** — `POST /api/chat` (SSE) streams `meta` → `delta` → `done`
  in that order; `meta` carries `model`, `delta` carries `text`. Skips if the provider is empty.
- **test_chat_empty_message_rejected** — a whitespace-only message → JSON `400` with `error`
  (rejected before streaming/billing).

### `TestCouncil`
- **test_council_sse_plan_steps** — `POST /api/chat {council:true}` (SSE) emits `council_plan`
  (with a `members` list) before any provider call, then `council_step`/`meta`/`done`. Skips if
  there are no available models/keys or the advisors didn't answer.

### `TestSearchChats`
- **test_search_chats_shape** — `POST /api/search_chats {user,q}` → `200` with
  `{results, count, q}`; `count == len(results)` and `q` is echoed back.

### `TestWorkflow`
- **test_workflow_get_templates** — `GET /api/workflow` → `{templates:[…]}` where each template
  has `id, title, desc, steps`; asserts the built-in `rewrite-polish` template exists.
- **test_workflow_run_ok** — `POST /api/workflow` runs the single-step `rewrite-polish` template
  → HTTP `200` with `{ok:true, steps:[…], result}` and a non-empty last-step `output`. Skips on
  empty-provider `ok:false`.

### `TestSelftest`
- **test_selftest_owner_ok** — `POST /api/selftest` as owner → `200` with
  `{ok, passed, failed, total_ms, checks[]}`; each check has `name, ok, ms, detail`, and
  `passed + failed == len(checks)`.

### `TestRag`
- **test_rag_ingest_then_query** — `POST /api/rag_ingest {user,name,text}` → `{ok:true, doc,
  chunks>=1, docs}`, then `POST /api/rag_query {user,query,k}` → `{hits, docs}` with at least one
  hit whose `doc`/`text` is present. Cleans up the test doc via `/api/rag_delete` afterward.
  Skips if the embedding provider is unavailable (`502`).

### `TestOrchestrate`
- **test_orchestrate_returns_final** — `POST /api/orchestrate {user,task}` → `200` with
  `{plan, results, final, steps}` and a non-empty `final`. Skips on `402/502/503` or empty provider.
- **test_orchestrate_empty_task_400** — empty `task` → `400` (validated before any model call).

### `TestOwnerGates`
- **test_selftest_non_owner_403** — `POST /api/selftest` as `stranger123` → `403`.
- **test_memory_consolidate_non_owner_403** — `POST /api/memory_consolidate` as `stranger123` → `403`.
- **test_run_code_non_owner_403** — `POST /api/run` as `stranger123` → `403` (anti-RCE gate).

### `TestInputValidation`
- **test_too_many_messages_400** — `401` messages in `POST /api/chat` → `400` (`SEC_MAX_MESSAGES = 400`).
- **test_oversized_payload_400** — `~4.1 MB` of message text → `400` (`SEC_MAX_TOTAL_CHARS = 4_000_000`).

## Notes

- The owner-gate tests use the user id `stranger123`, which is a non-owner because
  `server.is_owner` only treats `default` (or a user flagged `owner`) as the owner.
- These tests never `git commit`/`add`/`push` and never restart or kill the backend.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тайга ИИ — endpoint smoke-test suite (stdlib-only: unittest + urllib, NO pip deps).

Runs against the LIVE backend (server.py on port 8777). This is a real, founder-grade
smoke test: it checks status codes, JSON keys, and SSE event ordering against the actual
endpoint shapes in server.py — not trivially-true assertions.

Robustness rules (so the suite is useful even when providers are dry):
  * If the backend is unreachable → the whole class is SKIPPED (not failed) with a clear message.
  * If a test needs a model/provider that has no key or no balance → that single test is
    SKIPPED (detected via the SSE {"type":"error", ...} event or a JSON 402/error), not failed.
  * Structural assertions (status codes, JSON shape, SSE event TYPES that the server emits
    BEFORE touching a provider, owner-gates, input-validation) are always asserted hard —
    those do not depend on provider balance.

Run from repo root, with the backend running:
    python3 -m unittest tests.test_endpoints -v

Env vars:
    TAIGA_BASE   — backend base URL (default http://127.0.0.1:8777)
    TAIGA_OWNER  — owner user id (default "default" — owner per server.is_owner)
    TAIGA_SLOW   — per-request timeout seconds for model calls (default 120)
"""

import json
import os
import unittest
import urllib.error
import urllib.parse
import urllib.request

BASE = os.environ.get("TAIGA_BASE", "http://127.0.0.1:8777").rstrip("/")
OWNER = os.environ.get("TAIGA_OWNER", "default")
NON_OWNER = "stranger123"            # любой uid != default и без owner-флага = НЕ владелец
SLOW = float(os.environ.get("TAIGA_SLOW", "120"))
FAST = 15.0                          # для дешёвых нестриминговых ручек


# --------------------------------------------------------------------------- helpers

class Resp:
    """Лёгкая обёртка над ответом: code + (json|text)."""
    def __init__(self, code, body_bytes, headers):
        self.code = code
        self.headers = headers
        self.raw = body_bytes
        self.text = body_bytes.decode("utf-8", "replace")
        try:
            self.json = json.loads(self.text)
        except Exception:
            self.json = None


def _request(method, path, payload=None, timeout=FAST):
    """Базовый HTTP-вызов. Возвращает Resp даже на 4xx/5xx (urllib иначе кидает HTTPError)."""
    url = BASE + path
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return Resp(r.getcode(), r.read(), dict(r.headers))
    except urllib.error.HTTPError as e:
        return Resp(e.code, e.read(), dict(e.headers))


def get(path, timeout=FAST):
    return _request("GET", path, None, timeout)


def post(path, payload, timeout=FAST):
    return _request("POST", path, payload, timeout)


def _backend_up():
    try:
        r = get("/api/init?user=" + OWNER, timeout=FAST)
        return r.code == 200
    except Exception:
        return False


def sse_events(path, payload, timeout=SLOW, stop_on=("done", "error"), max_events=4000):
    """
    POST an SSE endpoint and parse `data: {json}\\n\\n` lines into a list of event dicts.
    Returns (events, error_msg|None). Stops once it sees an event whose type is in stop_on
    (or the stream ends / max_events reached). error_msg is set when an {type:"error"} event
    is seen, so callers can SKIP on no-balance / no-key instead of failing.
    """
    url = BASE + path
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"}, method="POST")
    events = []
    err = None
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            # сервер должен явно отдать event-stream для стриминговых ручек
            ctype = (r.headers.get("Content-Type") or "").lower()
            if "text/event-stream" not in ctype:
                # не-SSE ответ (например JSON 400 на пустое сообщение) — отдаём как один «json»-эвент
                body = r.read().decode("utf-8", "replace")
                try:
                    return [{"type": "_json", "_payload": json.loads(body), "_code": r.getcode()}], None
                except Exception:
                    return [{"type": "_raw", "_text": body, "_code": r.getcode()}], None
            for raw in r:
                line = raw.decode("utf-8", "replace").rstrip("\n").rstrip("\r")
                if not line.startswith("data:"):
                    continue
                chunk = line[len("data:"):].strip()
                if not chunk:
                    continue
                try:
                    ev = json.loads(chunk)
                except Exception:
                    continue
                events.append(ev)
                t = ev.get("type")
                if t == "error":
                    err = ev.get("message") or ev.get("error") or "error event"
                if t in stop_on or len(events) >= max_events:
                    break
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        try:
            return [{"type": "_json", "_payload": json.loads(body), "_code": e.code}], None
        except Exception:
            return [{"type": "_raw", "_text": body, "_code": e.code}], None
    return events, err


def types_of(events):
    return [e.get("type") for e in events]


# Маркеры «провайдер пуст / нет ключа / нет денег» — повод ПРОПУСТИТЬ тест, не ронять.
_SKIP_MARKERS = (
    "баланс", "balance", "пополни", "недостаточно", "insufficient",
    "нет ключа", "no key", "ключа для", "квот", "quota",
    "не ответили", "попробуй ещё раз", "временно недоступ",
    "слишком часто",  # rate-limit при многократном прогоне — не структурный провал
)


def _looks_like_no_provider(msg):
    if not msg:
        return False
    low = str(msg).lower()
    return any(m in low for m in _SKIP_MARKERS)


# --------------------------------------------------------------------------- base

class TaigaBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not _backend_up():
            raise unittest.SkipTest(
                "Backend недоступен на %s — запусти server.py (порт 8777) и повтори." % BASE)


# --------------------------------------------------------------------------- tests

class TestInit(TaigaBase):
    def test_init_200_and_keys(self):
        """/api/init GET → 200 + ожидаемые ключи витрины/каталога/биллинга."""
        r = get("/api/init?user=" + OWNER)
        self.assertEqual(r.code, 200, "init должен вернуть 200")
        self.assertIsNotNone(r.json, "init должен вернуть JSON")
        for key in ("users", "models", "full", "system", "keys",
                    "balance", "balances", "billing", "byok", "settings", "memory"):
            self.assertIn(key, r.json, "init: нет ожидаемого ключа %r" % key)
        self.assertIsInstance(r.json["models"], list, "init.models должен быть списком")
        self.assertIsInstance(r.json["billing"], dict, "init.billing должен быть объектом")
        # owner-флаг в billing должен подтверждать, что default = владелец
        self.assertTrue(r.json["billing"].get("owner") is True,
                        "init.billing.owner должен быть True для владельца")


class TestChat(TaigaBase):
    def test_chat_sse_meta_delta_done(self):
        """/api/chat POST SSE стримит meta → delta → done (или error при пустом провайдере → skip)."""
        payload = {"user": OWNER, "model": "__auto__",
                   "messages": [{"role": "user", "content": "Скажи ровно: привет"}]}
        events, err = sse_events("/api/chat", payload, timeout=SLOW)
        if err and _looks_like_no_provider(err):
            self.skipTest("chat: провайдер недоступен/пуст → %s" % err)
        ts = types_of(events)
        self.assertIn("meta", ts, "chat должен прислать событие meta. Получено: %s" % ts)
        self.assertIn("done", ts, "chat должен завершиться событием done. Получено: %s" % ts)
        # meta должна идти ДО done
        self.assertLess(ts.index("meta"), ts.index("done"), "meta должна предшествовать done")
        # meta несёт имя реально отвечающей модели
        meta = next(e for e in events if e.get("type") == "meta")
        self.assertIn("model", meta, "событие meta должно содержать поле model")
        # если был хоть один delta — он между meta и done
        if "delta" in ts:
            self.assertLess(ts.index("meta"), ts.index("delta"))
            self.assertLess(ts.index("delta"), ts.index("done"))
            d = next(e for e in events if e.get("type") == "delta")
            self.assertIn("text", d, "событие delta должно содержать поле text")

    def test_chat_empty_message_rejected(self):
        """Пустое сообщение → backend отбивает JSON-400 ДО стрима/биллинга."""
        r = post("/api/chat", {"user": OWNER, "messages": [{"role": "user", "content": "   "}]})
        self.assertEqual(r.code, 400, "пустое сообщение должно дать 400")
        self.assertIsNotNone(r.json)
        self.assertIn("error", r.json)


class TestCouncil(TaigaBase):
    def test_council_sse_plan_steps(self):
        """council-режим (council:true) стримит council_plan → council_step → … (meta/done или error→skip)."""
        payload = {"user": OWNER, "council": True, "n": 2,
                   "messages": [{"role": "user", "content": "Назови столицу Франции одним словом."}]}
        events, err = sse_events("/api/chat", payload, timeout=SLOW)
        ts = types_of(events)
        # council_plan эмитится ДО любого обращения к провайдеру — структурно обязателен,
        # КРОМЕ случая, когда вообще нет моделей/ключей (тогда сразу error → skip).
        if err and _looks_like_no_provider(err) and "council_plan" not in ts:
            self.skipTest("council: нет доступных моделей/ключей → %s" % err)
        self.assertIn("council_plan", ts,
                      "council должен прислать council_plan. Получено: %s" % ts)
        plan = next(e for e in events if e.get("type") == "council_plan")
        self.assertIn("members", plan, "council_plan должен содержать список members")
        self.assertIsInstance(plan["members"], list)
        # дальше: если советники ответили — будет meta(synth)+done; если нет — error (skip)
        if err and _looks_like_no_provider(err):
            self.skipTest("council: советники не ответили (пустой провайдер) → %s" % err)
        # если стрим дошёл до синтеза — порядок meta→done соблюдён
        if "done" in ts and "meta" in ts:
            self.assertLess(ts.index("meta"), ts.index("done"))


class TestSearchChats(TaigaBase):
    def test_search_chats_shape(self):
        """/api/search_chats POST {user,q} → {results, count, q}; count == len(results)."""
        r = post("/api/search_chats", {"user": OWNER, "q": "тест"})
        self.assertEqual(r.code, 200)
        self.assertIsNotNone(r.json)
        for k in ("results", "count", "q"):
            self.assertIn(k, r.json, "search_chats: нет ключа %r" % k)
        self.assertIsInstance(r.json["results"], list)
        self.assertEqual(r.json["count"], len(r.json["results"]),
                         "count должен совпадать с числом results")
        self.assertEqual(r.json["q"], "тест", "q должен эхо-возвращаться")


class TestWorkflow(TaigaBase):
    def test_workflow_get_templates(self):
        """/api/workflow GET → {templates:[...]} с полями id/title/desc/steps."""
        r = get("/api/workflow")
        self.assertEqual(r.code, 200)
        self.assertIsNotNone(r.json)
        self.assertIn("templates", r.json)
        tpls = r.json["templates"]
        self.assertIsInstance(tpls, list)
        self.assertGreater(len(tpls), 0, "должен быть хотя бы один встроенный шаблон")
        for t in tpls:
            for k in ("id", "title", "desc", "steps"):
                self.assertIn(k, t, "шаблон без ключа %r: %r" % (k, t))
        # известный однотшаговый шаблон должен присутствовать
        ids = [t["id"] for t in tpls]
        self.assertIn("rewrite-polish", ids,
                      "ожидался шаблон rewrite-polish. Есть: %s" % ids)

    def test_workflow_run_ok(self):
        """/api/workflow POST шаблон rewrite-polish (один chat-шаг) → {ok, steps, result} или error→skip."""
        payload = {"user": OWNER, "template_id": "rewrite-polish",
                   "input": "перепеши это: превед как дила"}
        r = post("/api/workflow", payload, timeout=SLOW)
        # workflow всегда отдаёт HTTP 200 (ошибки внутри тела как ok:false)
        self.assertEqual(r.code, 200, "workflow должен вернуть HTTP 200")
        self.assertIsNotNone(r.json)
        self.assertIn("ok", r.json)
        self.assertIn("steps", r.json)
        if not r.json["ok"]:
            if _looks_like_no_provider(r.json.get("error")):
                self.skipTest("workflow: провайдер недоступен/пуст → %s" % r.json.get("error"))
            self.fail("workflow вернул ok:false по нерпровайдерной причине: %s" % r.json.get("error"))
        self.assertIn("result", r.json)
        self.assertIsInstance(r.json["steps"], list)
        self.assertGreater(len(r.json["steps"]), 0, "должен быть хотя бы один выполненный шаг")
        self.assertIn("output", r.json["steps"][-1])


class TestSelftest(TaigaBase):
    def test_selftest_owner_ok(self):
        """/api/selftest POST (owner) → {ok, passed, failed, total_ms, checks[]}."""
        r = post("/api/selftest", {"user": OWNER}, timeout=SLOW)
        self.assertEqual(r.code, 200, "selftest для владельца должен дать 200")
        self.assertIsNotNone(r.json)
        for k in ("ok", "passed", "failed", "total_ms", "checks"):
            self.assertIn(k, r.json, "selftest: нет ключа %r" % k)
        self.assertIsInstance(r.json["checks"], list)
        self.assertGreater(len(r.json["checks"]), 0, "selftest должен прогнать хотя бы один чек")
        for c in r.json["checks"]:
            for k in ("name", "ok", "ms", "detail"):
                self.assertIn(k, c, "чек без ключа %r: %r" % (k, c))
        # passed+failed == число чеков
        self.assertEqual(r.json["passed"] + r.json["failed"], len(r.json["checks"]),
                         "passed+failed должно равняться числу чеков")


class TestRag(TaigaBase):
    def test_rag_ingest_then_query(self):
        """RAG: ingest текста → query тем же ключевым словом возвращает hits с doc-привязкой."""
        marker = "тайга_ tест_ маркер_ оранжевый_ носорог"
        name = "taiga_smoke_doc.txt"
        text = ("Это тестовый документ для смоук-теста RAG. "
                "Секретное кодовое слово: %s. "
                "Остальной текст наполнения, чтобы был контекст для эмбеддингов." % marker)
        ing = post("/api/rag_ingest", {"user": OWNER, "name": name, "text": text}, timeout=SLOW)
        # ingest может упасть на отсутствии эмбеддинг-провайдера → 502; тогда skip
        if ing.code == 502 or (ing.json and _looks_like_no_provider(ing.json.get("error"))):
            self.skipTest("rag_ingest: эмбеддинг-провайдер недоступен → %s"
                          % (ing.json.get("error") if ing.json else ing.code))
        self.assertEqual(ing.code, 200, "rag_ingest должен дать 200 при наличии провайдера")
        self.assertIsNotNone(ing.json)
        self.assertTrue(ing.json.get("ok"), "rag_ingest.ok должен быть True")
        for k in ("doc", "chunks", "docs"):
            self.assertIn(k, ing.json, "rag_ingest: нет ключа %r" % k)
        self.assertGreaterEqual(ing.json["chunks"], 1, "должен создаться хотя бы один чанк")

        try:
            q = post("/api/rag_query",
                     {"user": OWNER, "query": "кодовое слово оранжевый носорог", "k": 4},
                     timeout=SLOW)
            if q.code == 502 or (q.json and _looks_like_no_provider(q.json.get("error"))):
                self.skipTest("rag_query: эмбеддинг-провайдер недоступен → %s"
                              % (q.json.get("error") if q.json else q.code))
            self.assertEqual(q.code, 200)
            self.assertIsNotNone(q.json)
            self.assertIn("hits", q.json, "rag_query должен вернуть hits")
            self.assertIn("docs", q.json, "rag_query должен вернуть docs")
            self.assertIsInstance(q.json["hits"], list)
            self.assertGreater(len(q.json["hits"]), 0,
                               "после ingest запрос по ключу должен дать хотя бы один hit")
            top = q.json["hits"][0]
            self.assertIn("doc", top, "hit должен ссылаться на doc")
            self.assertIn("text", top, "hit должен содержать text")
        finally:
            # уборка: удаляем тестовый документ, чтобы не засорять базу владельца
            try:
                post("/api/rag_delete", {"user": OWNER, "name": name}, timeout=FAST)
            except Exception:
                pass


class TestOrchestrate(TaigaBase):
    def test_orchestrate_returns_final(self):
        """/api/orchestrate POST {user,task} → {plan, results, final, steps} (или error/402 → skip)."""
        payload = {"user": OWNER, "task": "В одном предложении: что такое HTTP?"}
        r = post("/api/orchestrate", payload, timeout=SLOW)
        if r.code in (402, 502, 503):
            self.skipTest("orchestrate: недоступен/нет баланса (HTTP %s) → %s"
                          % (r.code, (r.json or {}).get("error")))
        self.assertEqual(r.code, 200, "orchestrate должен вернуть 200 при доступном провайдере")
        self.assertIsNotNone(r.json)
        if "error" in r.json and _looks_like_no_provider(r.json.get("error")):
            self.skipTest("orchestrate: провайдер пуст → %s" % r.json.get("error"))
        for k in ("plan", "results", "final", "steps"):
            self.assertIn(k, r.json, "orchestrate: нет ключа %r" % k)
        self.assertIsInstance(r.json["results"], list)
        self.assertIsInstance(r.json["steps"], list)
        self.assertTrue(str(r.json.get("final") or "").strip(),
                        "orchestrate.final не должен быть пустым при успешном прогоне")

    def test_orchestrate_empty_task_400(self):
        """Пустая задача → 400 (валидация ДО любого вызова модели)."""
        r = post("/api/orchestrate", {"user": OWNER, "task": "   "})
        self.assertEqual(r.code, 400, "пустая task должна дать 400")
        self.assertIsNotNone(r.json)
        self.assertIn("error", r.json)


class TestOwnerGates(TaigaBase):
    def test_selftest_non_owner_403(self):
        """/api/selftest для НЕ-владельца → 403."""
        r = post("/api/selftest", {"user": NON_OWNER})
        self.assertEqual(r.code, 403, "selftest для не-владельца должен дать 403")
        self.assertIsNotNone(r.json)
        self.assertIn("error", r.json)

    def test_memory_consolidate_non_owner_403(self):
        """/api/memory_consolidate для НЕ-владельца → 403."""
        r = post("/api/memory_consolidate", {"user": NON_OWNER})
        self.assertEqual(r.code, 403, "memory_consolidate для не-владельца должен дать 403")
        self.assertIsNotNone(r.json)
        self.assertIn("error", r.json)

    def test_run_code_non_owner_403(self):
        """/api/run (код-интерпретатор) для НЕ-владельца → 403 (анти-RCE гейт)."""
        r = post("/api/run", {"user": NON_OWNER, "code": "print(1)", "lang": "python"})
        self.assertEqual(r.code, 403, "запуск кода не-владельцем должен дать 403")
        self.assertIsNotNone(r.json)
        self.assertIn("error", r.json)


class TestInputValidation(TaigaBase):
    def test_too_many_messages_400(self):
        """>400 сообщений в /api/chat → 400 (грубая защита размера входа)."""
        msgs = [{"role": "user", "content": "x"} for _ in range(401)]
        r = post("/api/chat", {"user": OWNER, "messages": msgs})
        self.assertEqual(r.code, 400, "401 сообщение должно дать 400")
        self.assertIsNotNone(r.json)
        self.assertIn("error", r.json)
        self.assertIn("сообщ", r.json["error"].lower(),
                      "ошибка должна быть про число сообщений: %s" % r.json["error"])

    def test_oversized_payload_400(self):
        """>4 МБ суммарного текста в /api/chat → 400 (потолок SEC_MAX_TOTAL_CHARS)."""
        big = "а" * (4_100_000)        # ~4.1 МБ одной строкой > 4_000_000 потолка
        r = post("/api/chat", {"user": OWNER, "messages": [{"role": "user", "content": big}]},
                 timeout=SLOW)
        self.assertEqual(r.code, 400, "сверхбольшой payload должен дать 400")
        self.assertIsNotNone(r.json)
        self.assertIn("error", r.json)


if __name__ == "__main__":
    unittest.main(verbosity=2)

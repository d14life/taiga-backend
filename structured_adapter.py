"""
structured_adapter — асинхронный адаптер цепочки «сырой ввод → агрегация → структурированный вывод».

Идея «прозрачной трансформации ввода»:
    Пользователь шлёт «шероховатый» запрос (опечатки, обрывки, недосказанность, мешанина языков).
    Адаптер НЕ показывает эту сырость основной (frontier) модели. Вместо этого он:
      1) нормализует ввод дешёвой моделью в чёткую задачу + метаданные (stage: normalize);
      2) собирает строгий StructuredContext (JSON-обёртка: задача, schema hints, routing, метаданные);
      3) по task_type выбирает маршрут (model_id/temp/max_tokens) — implicit task routing;
      4) отправляет в frontier-модель запрос на ВЫВОД СТРОГО ПО СХЕМЕ (stage: generate);
      5) извлекает и валидирует артефакт по целевой Pydantic-схеме, с retry на ошибках валидации.

Стек: Python 3.11+, asyncio, Pydantic v2, httpx, typed interfaces, config-driven routing,
retry (транспортный + валидационный), structured JSON-логирование. Внешний бэкенд абстрагирован
протоколом ChatBackend — модуль тестируется без сети (см. adapter_example.py).
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Generic, Protocol, TypeVar, runtime_checkable

import httpx
from pydantic import BaseModel, Field, ValidationError, field_validator

# ──────────────────────────────────────────────────────────── structured logging

class _JsonFormatter(logging.Formatter):
    """Каждая строка лога — самостоятельный JSON-объект (machine-readable)."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }
        # всё, что положили через logger.info(..., extra={"fields": {...}})
        fields = getattr(record, "fields", None)
        if isinstance(fields, dict):
            payload.update(fields)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def get_logger(name: str = "mostik.adapter", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler()
        h.setFormatter(_JsonFormatter())
        logger.addHandler(h)
        logger.setLevel(level)
        logger.propagate = False
    return logger


log = get_logger()


def _emit(logger: logging.Logger, level: int, event: str, **fields: Any) -> None:
    logger.log(level, event, extra={"fields": fields})


# ──────────────────────────────────────────────────────────── доменные модели

class TaskType(str, Enum):
    CODE = "code"
    CONFIG = "config"
    TEXT = "text"
    DATA = "data"
    UNKNOWN = "unknown"


class RawInput(BaseModel):
    """Необработанный/деградированный пользовательский ввод."""
    text: str = Field(min_length=1)
    user_id: str | None = None
    hints: dict[str, Any] = Field(default_factory=dict)  # подсказки от вызывающего кода

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()[:16]


class ContextMetadata(BaseModel):
    language: str = "unknown"
    raw_length: int = 0
    detected_intent: str = ""
    routing_key: str = "default"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class NormalizationResult(BaseModel):
    """Что возвращает stage normalize — чистая задача без «шероховатости»."""
    task_type: TaskType = TaskType.UNKNOWN
    normalized_instruction: str = Field(min_length=1)
    target_summary: str = ""
    language: str = "unknown"
    detected_intent: str = ""

    @field_validator("task_type", mode="before")
    @classmethod
    def _coerce_task(cls, v: Any) -> Any:
        if isinstance(v, str):
            v = v.strip().lower()
            return v if v in TaskType._value2member_map_ else TaskType.UNKNOWN.value
        return v


class StructuredContext(BaseModel):
    """Строгая JSON-обёртка, которую видит frontier-модель (исходный сырой текст — НЕ видит)."""
    task_type: TaskType
    normalized_instruction: str
    schema_hint: dict[str, Any]
    metadata: ContextMetadata
    original_fingerprint: str          # хэш сырого ввода — только для трассировки


T = TypeVar("T", bound=BaseModel)


class AdapterResult(BaseModel, Generic[T]):
    """Итог: валидный артефакт + полная трасса прогона."""
    artifact: T
    context: StructuredContext
    attempts: int
    latency_ms: int
    usage: dict[str, int] = Field(default_factory=dict)


class AdapterError(RuntimeError):
    """Не удалось получить валидный артефакт после всех ретраев."""


# ──────────────────────────────────────────────────────────── конфиг (config-driven routing)

class ModelRoute(BaseModel):
    model_id: str
    temperature: float = 0.4
    max_tokens: int = 2048
    json_mode: bool = True             # response_format=json_object, если бэкенд умеет


class AdapterConfig(BaseModel):
    base_url: str = "https://api.venice.ai/api/v1"
    api_key_env: str = "VENICE_API_KEY"     # имя env-переменной с ключом (сам ключ в коде не хранится)
    routes: dict[str, ModelRoute]            # routing_key → маршрут
    default_route: str = "default"
    normalizer_route: str = "normalizer"
    max_validation_retries: int = 3
    max_transport_retries: int = 3
    timeout_s: float = 120.0

    def route_for(self, key: str) -> ModelRoute:
        return self.routes.get(key) or self.routes[self.default_route]

    @classmethod
    def from_toml(cls, path: str) -> "AdapterConfig":
        import tomllib
        with open(path, "rb") as f:
            return cls.model_validate(tomllib.load(f))


# ──────────────────────────────────────────────────────────── бэкенд (абстракция транспорта)

class ChatMessage(BaseModel):
    role: str
    content: str


@runtime_checkable
class ChatBackend(Protocol):
    """Минимальный контракт LLM-бэкенда. Любой OpenAI-совместимый провайдер подходит;
    стаб для тестов реализует тот же метод без сети."""

    async def complete(self, route: ModelRoute, messages: list[ChatMessage]) -> tuple[str, dict[str, int]]:
        ...


def _is_transient(exc: Exception) -> bool:
    if isinstance(exc, (httpx.TimeoutException, httpx.TransportError)):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in (408, 409, 429, 500, 502, 503, 504)
    return False


async def _retry_transport(fn, *, attempts: int, base_delay: float, logger: logging.Logger):
    """Экспоненциальный backoff на транзиентных сетевых ошибках/429/5xx."""
    last: Exception | None = None
    for i in range(1, attempts + 1):
        try:
            return await fn()
        except Exception as e:  # noqa: BLE001 — решаем по _is_transient
            last = e
            if not _is_transient(e) or i == attempts:
                raise
            delay = base_delay * (2 ** (i - 1))
            _emit(logger, logging.WARNING, "transport.retry", attempt=i, delay_s=round(delay, 2),
                  error=type(e).__name__)
            await asyncio.sleep(delay)
    assert last is not None
    raise last


class OpenAICompatibleBackend:
    """httpx-бэкенд для OpenAI-совместимого /chat/completions (Venice, Featherless, OpenAI…)."""

    def __init__(self, config: AdapterConfig, logger: logging.Logger | None = None) -> None:
        self._cfg = config
        self._log = logger or log
        key = os.environ.get(config.api_key_env, "")
        if not key:
            raise AdapterError(f"нет ключа в env: {config.api_key_env}")
        self._client = httpx.AsyncClient(
            base_url=config.base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            timeout=config.timeout_s,
        )

    async def complete(self, route: ModelRoute, messages: list[ChatMessage]) -> tuple[str, dict[str, int]]:
        body: dict[str, Any] = {
            "model": route.model_id,
            "messages": [m.model_dump() for m in messages],
            "temperature": route.temperature,
            "max_tokens": route.max_tokens,
        }
        if route.json_mode:
            body["response_format"] = {"type": "json_object"}

        async def _call() -> httpx.Response:
            r = await self._client.post("/chat/completions", json=body)
            # не все модели умеют response_format — мягко деградируем без него
            if r.status_code == 400 and "response_format" in body and "response_format" in r.text:
                _emit(self._log, logging.WARNING, "json_mode.unsupported", model=route.model_id)
                body.pop("response_format", None)
                r = await self._client.post("/chat/completions", json=body)
            r.raise_for_status()
            return r

        resp = await _retry_transport(
            _call, attempts=self._cfg.max_transport_retries, base_delay=0.8, logger=self._log)
        data = resp.json()
        text = data["choices"][0]["message"].get("content") or ""
        usage = {k: int(v) for k, v in (data.get("usage") or {}).items() if isinstance(v, int)}
        return text, usage

    async def aclose(self) -> None:
        await self._client.aclose()


# ──────────────────────────────────────────────────────────── утилиты

_FENCE = re.compile(r"```(?:json)?|```", re.I)


def extract_json(text: str) -> dict[str, Any]:
    """Достаёт первый валидный JSON-объект из ответа модели (срезает спец-токены и фенсы)."""
    s = re.sub(r"<\|[^|<>]*\|>", " ", text)
    s = _FENCE.sub(" ", s).strip()
    start = s.find("{")
    if start == -1:
        raise ValueError("в ответе нет JSON-объекта")
    obj, _ = json.JSONDecoder().raw_decode(s[start:])
    if not isinstance(obj, dict):
        raise ValueError("верхний уровень JSON — не объект")
    return obj


def _guess_language(text: str) -> str:
    cyr = len(re.findall(r"[а-яёА-ЯЁ]", text))
    lat = len(re.findall(r"[a-zA-Z]", text))
    if cyr == 0 and lat == 0:
        return "unknown"
    return "ru" if cyr >= lat else "en"


# ──────────────────────────────────────────────────────────── ядро адаптера

_NORMALIZE_SYSTEM = (
    "Ты — нормализатор запросов. На вход приходит СЫРОЙ пользовательский запрос: возможны "
    "опечатки, обрывки, смешение языков, недосказанность. Твоя задача — превратить его в чёткую, "
    "однозначную постановку задачи, НЕ выполняя её. Определи тип задачи (code/config/text/data), "
    "восстанови намерение, опиши целевой результат.\n"
    "Верни СТРОГО JSON-объект с полями: "
    '{"task_type": "...", "normalized_instruction": "...", "target_summary": "...", '
    '"language": "ru|en", "detected_intent": "..."}. Без пояснений и без markdown.'
)

_GENERATE_SYSTEM = (
    "Ты — генератор структурированных артефактов. Тебе дают ЧЁТКУЮ задачу и JSON Schema целевого "
    "результата. Верни ТОЛЬКО валидный JSON-объект строго по этой схеме — без markdown, без "
    "комментариев, без полей вне схемы. Если в схеме есть поле для кода/конфига/текста — положи "
    "итоговый артефакт туда как строку."
)


class StructuredAdapter(Generic[T]):
    """Связывает stage normalize → routing → stage generate → валидацию артефакта по схеме T."""

    def __init__(
        self,
        artifact_model: type[T],
        config: AdapterConfig,
        backend: ChatBackend,
        logger: logging.Logger | None = None,
    ) -> None:
        self._model = artifact_model
        self._cfg = config
        self._backend = backend
        self._log = logger or log
        self._schema = artifact_model.model_json_schema()

    # -- stage 1: прозрачная нормализация сырого ввода --
    async def _normalize(self, raw: RawInput) -> NormalizationResult:
        messages = [
            ChatMessage(role="system", content=_NORMALIZE_SYSTEM),
            ChatMessage(role="user", content=raw.text),
        ]
        route = self._cfg.route_for(self._cfg.normalizer_route)
        text, usage = await self._backend.complete(route, messages)
        try:
            result = NormalizationResult.model_validate(extract_json(text))
        except (ValueError, ValidationError) as e:
            # дешёвая модель не справилась с JSON — мягкий фолбэк: берём сырой текст как инструкцию
            _emit(self._log, logging.WARNING, "normalize.fallback", fp=raw.fingerprint,
                  error=str(e)[:120])
            result = NormalizationResult(
                task_type=TaskType.UNKNOWN,
                normalized_instruction=raw.text.strip(),
                language=_guess_language(raw.text),
            )
        _emit(self._log, logging.INFO, "normalize.done", fp=raw.fingerprint,
              task_type=result.task_type.value, route=route.model_id, usage=usage)
        return result

    # -- сборка строгого контекста --
    def _build_context(self, raw: RawInput, norm: NormalizationResult) -> StructuredContext:
        routing_key = raw.hints.get("routing_key") or norm.task_type.value
        meta = ContextMetadata(
            language=norm.language or _guess_language(raw.text),
            raw_length=len(raw.text),
            detected_intent=norm.detected_intent,
            routing_key=routing_key,
        )
        return StructuredContext(
            task_type=norm.task_type,
            normalized_instruction=norm.normalized_instruction,
            schema_hint=self._schema,
            metadata=meta,
            original_fingerprint=raw.fingerprint,
        )

    # -- stage 2+3: генерация по схеме + валидация с retry --
    async def _generate(self, ctx: StructuredContext) -> tuple[T, int, dict[str, int]]:
        route = self._cfg.route_for(ctx.metadata.routing_key)
        base_user = (
            f"ЗАДАЧА:\n{ctx.normalized_instruction}\n\n"
            f"ТИП: {ctx.task_type.value}\n\n"
            f"JSON SCHEMA целевого результата:\n{json.dumps(ctx.schema_hint, ensure_ascii=False)}\n\n"
            "Верни только JSON по схеме."
        )
        messages = [
            ChatMessage(role="system", content=_GENERATE_SYSTEM),
            ChatMessage(role="user", content=base_user),
        ]
        total_usage: dict[str, int] = {}
        last_err = ""
        for attempt in range(1, self._cfg.max_validation_retries + 1):
            text, usage = await self._backend.complete(route, messages)
            for k, v in usage.items():
                total_usage[k] = total_usage.get(k, 0) + v
            try:
                artifact = self._model.model_validate(extract_json(text))
                _emit(self._log, logging.INFO, "generate.ok", fp=ctx.original_fingerprint,
                      route=route.model_id, attempt=attempt, usage=usage)
                return artifact, attempt, total_usage
            except (ValueError, ValidationError) as e:
                last_err = str(e)[:400]
                _emit(self._log, logging.WARNING, "generate.invalid", fp=ctx.original_fingerprint,
                      attempt=attempt, error=last_err)
                # подаём модели её же ошибку валидации — самокоррекция
                messages.append(ChatMessage(role="assistant", content=text[:2000]))
                messages.append(ChatMessage(role="user", content=(
                    f"Твой JSON не прошёл валидацию схемы: {last_err}\n"
                    "Верни ИСПРАВЛЕННЫЙ JSON строго по схеме, только JSON.")))
        raise AdapterError(f"артефакт не прошёл валидацию за {self._cfg.max_validation_retries} попыток: {last_err}")

    # -- публичный вход --
    async def run(self, raw: RawInput) -> AdapterResult[T]:
        t0 = time.monotonic()
        _emit(self._log, logging.INFO, "run.start", fp=raw.fingerprint,
              user_id=raw.user_id, raw_length=len(raw.text))
        norm = await self._normalize(raw)
        ctx = self._build_context(raw, norm)
        artifact, attempts, usage = await self._generate(ctx)
        latency_ms = int((time.monotonic() - t0) * 1000)
        _emit(self._log, logging.INFO, "run.done", fp=raw.fingerprint,
              attempts=attempts, latency_ms=latency_ms, usage=usage)
        return AdapterResult[self._model](
            artifact=artifact, context=ctx, attempts=attempts,
            latency_ms=latency_ms, usage=usage)


# ──────────────────────────────────────────────────────────── relay: uncensored → frontier → текст

class RelayResult(BaseModel):
    """Итог relay-режима: чем причёсан промпт и что ответила frontier-модель (обычным текстом)."""
    crafted_prompt: str
    answer: str
    normalizer_model: str
    responder_model: str
    latency_ms: int
    usage: dict[str, int] = Field(default_factory=dict)


async def prompt_relay(
    raw: RawInput,
    config: AdapterConfig,
    backend: ChatBackend,
    *,
    normalizer_key: str = "normalizer",      # маршрут «крафтера» промпта (напр. Qwen uncensored)
    responder_key: str = "default",          # маршрут отвечающего (напр. frontier-модель)
    system: str = "Ответь полно, по делу и на языке пользователя.",
    logger: logging.Logger | None = None,
) -> RelayResult:
    """Цепочка: uncensored-модель переписывает сырой промпт в чёткую задачу → frontier-модель
    отвечает свободным текстом → ответ возвращается тебе. Это НЕ обход чужих guardrails:
    crafter лишь делает промпт яснее/полнее, отвечает frontier-модель в своих рамках."""
    lg = logger or log
    t0 = time.monotonic()
    norm_route = config.route_for(normalizer_key)
    resp_route = config.route_for(responder_key).model_copy(update={"json_mode": False})

    # 1) uncensored-модель причёсывает промпт (frontier видит уже чистую задачу)
    craft_msgs = [ChatMessage(role="system", content=_NORMALIZE_SYSTEM),
                  ChatMessage(role="user", content=raw.text)]
    crafted_text, u1 = await backend.complete(norm_route, craft_msgs)
    try:
        crafted = NormalizationResult.model_validate(extract_json(crafted_text)).normalized_instruction
    except (ValueError, ValidationError):
        crafted = raw.text.strip()
    _emit(lg, logging.INFO, "relay.crafted", fp=raw.fingerprint, model=norm_route.model_id, usage=u1)

    # 2) frontier-модель отвечает свободным текстом
    ans_msgs = [ChatMessage(role="system", content=system),
                ChatMessage(role="user", content=crafted)]
    answer, u2 = await backend.complete(resp_route, ans_msgs)
    usage = {k: u1.get(k, 0) + u2.get(k, 0) for k in set(u1) | set(u2)}
    _emit(lg, logging.INFO, "relay.answered", fp=raw.fingerprint, model=resp_route.model_id, usage=u2)

    return RelayResult(
        crafted_prompt=crafted, answer=answer,
        normalizer_model=norm_route.model_id, responder_model=resp_route.model_id,
        latency_ms=int((time.monotonic() - t0) * 1000), usage=usage)


# ──────────────────────────────────────────────────────────── фабрика

def build_adapter(artifact_model: type[T], config: AdapterConfig,
                  logger: logging.Logger | None = None) -> tuple[StructuredAdapter[T], OpenAICompatibleBackend]:
    """Удобный конструктор: реальный httpx-бэкенд + адаптер. Не забудь backend.aclose()."""
    backend = OpenAICompatibleBackend(config, logger)
    return StructuredAdapter(artifact_model, config, backend, logger), backend

"""
Пример использования structured_adapter.

Запуск:
    python3 adapter_example.py          # оффлайн-демо на стаб-бэкенде (без сети, без денег)
    python3 adapter_example.py --live   # реальный прогон через Venice (нужен ~/.venice_key)

Демонстрирует «прозрачную трансформацию»: на вход — сырой, кривой запрос; на выходе —
строго типизированный артефакт, прошедший валидацию по Pydantic-схеме.
"""
import asyncio
import json
import os
import sys
from pathlib import Path

from pydantic import BaseModel, Field

from structured_adapter import (
    AdapterConfig, ChatMessage, ModelRoute, RawInput, StructuredAdapter,
    build_adapter, get_logger,
)


# ── 1. Описываем ЦЕЛЕВУЮ схему артефакта (то, что хотим получить строго типизированным) ──
class CodeArtifact(BaseModel):
    language: str = Field(description="язык программирования, напр. python")
    filename: str = Field(description="предлагаемое имя файла")
    code: str = Field(description="готовый код целиком", min_length=1)
    summary: str = Field(description="одно предложение: что делает код")


# ── 2. Стаб-бэкенд: имитирует ответы LLM детерминированно, чтобы проверить пайплайн без сети ──
class StubBackend:
    async def complete(self, route: ModelRoute, messages: list[ChatMessage]) -> tuple[str, dict[str, int]]:
        system = messages[0].content
        if "нормализатор" in system:                      # stage normalize
            return (json.dumps({
                "task_type": "code",
                "normalized_instruction": "Напиши на Python функцию is_prime(n: int) -> bool, "
                                          "проверяющую простоту числа, с обработкой n < 2.",
                "target_summary": "функция проверки простого числа",
                "language": "ru",
                "detected_intent": "сгенерировать функцию",
            }, ensure_ascii=False), {"prompt_tokens": 40, "completion_tokens": 30})
        # stage generate — первый ответ намеренно «битый» (нет поля summary) → проверим retry
        last_user = messages[-1].content
        if "не прошёл валидацию" in last_user:             # это уже ретрай — отдаём корректный
            return (json.dumps({
                "language": "python",
                "filename": "is_prime.py",
                "code": "def is_prime(n: int) -> bool:\n"
                        "    if n < 2:\n        return False\n"
                        "    i = 2\n    while i * i <= n:\n"
                        "        if n % i == 0:\n            return False\n"
                        "        i += 1\n    return True\n",
                "summary": "Проверяет, является ли целое число простым.",
            }, ensure_ascii=False), {"prompt_tokens": 120, "completion_tokens": 60})
        return (json.dumps({                                # первый (битый) ответ — без summary
            "language": "python",
            "filename": "is_prime.py",
            "code": "def is_prime(n): return n > 1",
        }, ensure_ascii=False), {"prompt_tokens": 110, "completion_tokens": 20})


# ── минимальный конфиг для демо ──
def demo_config() -> AdapterConfig:
    return AdapterConfig(
        base_url="https://api.venice.ai/api/v1",
        api_key_env="VENICE_API_KEY",
        routes={
            "normalizer": ModelRoute(model_id="gemma-4-uncensored", temperature=0.2, max_tokens=600),
            "default": ModelRoute(model_id="venice-uncensored-1-2", temperature=0.4, max_tokens=2048),
            "code": ModelRoute(model_id="qwen3-coder-480b-a35b-instruct-turbo", temperature=0.2, max_tokens=4096),
        },
    )


async def run_stub() -> None:
    cfg = demo_config()
    adapter: StructuredAdapter[CodeArtifact] = StructuredAdapter(CodeArtifact, cfg, StubBackend())
    raw = RawInput(text="напиши прайм чек фунцию питон n<2 учти плз", user_id="damir")
    result = await adapter.run(raw)
    print("\n=== АРТЕФАКТ (валидный, типизированный) ===")
    print("attempts:", result.attempts, "| latency_ms:", result.latency_ms, "| usage:", result.usage)
    print("task_type:", result.context.task_type.value, "| routing:", result.context.metadata.routing_key)
    print("normalized:", result.context.normalized_instruction)
    print("-" * 60)
    print(result.artifact.model_dump_json(indent=2))


async def run_live() -> None:
    # мост к реальному ключу: structured_adapter читает ключ из env VENICE_API_KEY
    key_file = Path("~/.venice_key").expanduser()
    if key_file.exists() and not os.environ.get("VENICE_API_KEY"):
        os.environ["VENICE_API_KEY"] = key_file.read_text().strip()
    cfg = AdapterConfig.from_toml(str(Path(__file__).parent / "adapter_config.toml"))
    adapter, backend = build_adapter(CodeArtifact, cfg)
    try:
        raw = RawInput(text="сделай питон функ что СЛИВАЕТ два отсортир списка в один отсортир, "
                            "без библиотек, тайпхинты", user_id="damir")
        result = await adapter.run(raw)
        print("\n=== LIVE АРТЕФАКТ ===")
        print("attempts:", result.attempts, "| latency_ms:", result.latency_ms, "| usage:", result.usage)
        print(result.artifact.model_dump_json(indent=2))
    finally:
        await backend.aclose()


if __name__ == "__main__":
    get_logger()  # включаем JSON-логи в stdout
    if "--live" in sys.argv:
        asyncio.run(run_live())
    else:
        asyncio.run(run_stub())

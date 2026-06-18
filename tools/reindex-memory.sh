#!/usr/bin/env bash
# reindex-memory.sh — держать память свежей + ЧИСТОЙ после правок доков/кода.
# graphify (граф кода) + gbrain (доки, NVIDIA-эмбеддинги) + ВЫЧИСТИТЬ _archive из gbrain
# (gbrain import тянет всё, поэтому архив надо удалять после каждого импорта).
# Запуск: bash tools/reindex-memory.sh   (из корня репо)
set -e
export PATH="/opt/homebrew/bin:$HOME/.bun/bin:$HOME/.local/bin:$PATH"
export OPENAI_API_KEY="$(grep -E '^NVIDIA_API_KEY=' ~/.reel-intelligence.env | head -1 | cut -d= -f2-)"
export OPENAI_BASE_URL="https://integrate.api.nvidia.com/v1"

echo "[1/3] graphify — пересборка графа кода (AST, без LLM)…"
graphify update . 2>&1 | tail -2

echo "[2/3] gbrain — переимпорт доков (NVIDIA-эмбеддинги)…"
gbrain import . 2>&1 | tail -3

echo "[3/3] чистка _archive из gbrain (только канон в памяти)…"
del=0
for f in _archive/*.md; do
  [ -e "$f" ] || continue
  slug="_archive/$(basename "$f" .md | tr 'A-Z' 'a-z')"
  gbrain delete "$slug" >/dev/null 2>&1 && del=$((del+1)) || true
done
echo "  удалено архивных страниц: $del"
echo "ГОТОВО — память свежая и только канон."

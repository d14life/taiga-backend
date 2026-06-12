#!/usr/bin/env bash
# Ночной смоук-тест бэкенда Тайги (координатор atlas). Дёшево: только гейты/каталог/RAG/поиск/браузер.
# НЕ тратит на supersearch/orchestrate/image-gen (это $$). Запуск: bash night-smoke.sh
B=127.0.0.1:8777
pass=0; fail=0
ok(){ echo "  ✅ $1"; pass=$((pass+1)); }
no(){ echo "  ❌ $1"; fail=$((fail+1)); }
j(){ python3 -c "import sys,json;d=json.load(sys.stdin);print($1)" 2>/dev/null; }

echo "=== TAIGA NIGHT SMOKE $(date +%H:%M:%S) ==="

# 1. catalog alive + image models ingested
c=$(curl -s --max-time 10 $B/api/catalog)
n=$(echo "$c" | python3 -c "import sys,json;m=json.load(sys.stdin);m=m.get('models',m) if isinstance(m,dict) else m;print(sum(1 for x in m if x.get('kind')=='image'))" 2>/dev/null)
[ "${n:-0}" -ge 200 ] && ok "catalog: $n image models" || no "catalog image models = ${n:-0} (<200)"

# 2. balances + low flag present
b=$(curl -s --max-time 8 "$B/api/init?user=default")
echo "$b" | python3 -c "import sys,json;d=json.load(sys.stdin);bs=d.get('balances',{});assert 'low' in next(iter(bs.values()))" 2>/dev/null \
  && ok "init: per-provider balances + low flag" || no "init: low flag missing"

# 3. test_topup hole CLOSED (non-owner → 503)
s=$(curl -s -o /dev/null -w "%{http_code}" -X POST $B/api/topup -H 'content-type: application/json' -d '{"user":"smoke_nonowner","rub":100}')
[ "$s" = "503" ] && ok "test_topup closed (non-owner 503)" || no "test_topup NOT closed (got $s)"

# 4. image $0 gate (non-owner zero balance → 402, no provider spend)
s=$(curl -s -o /dev/null -w "%{http_code}" -X POST $B/api/image -H 'content-type: application/json' -d '{"user":"smoke_broke","model":"venice-sd35","prompt":"x"}')
[ "$s" = "402" ] && ok "image \$0 gate (402, no spend)" || no "image gate got $s (expected 402)"

# 5. RAG ingest + query (tiny doc, ~\$0.00002 embeddings)
curl -s -X POST $B/api/rag_ingest -H 'content-type: application/json' \
  -d '{"user":"smoke_rag","name":"t.txt","text":"Кодовое слово проекта Тайга — ЗАРЯ-918."}' >/dev/null
hit=$(curl -s -X POST $B/api/rag_query -H 'content-type: application/json' -d '{"user":"smoke_rag","query":"кодовое слово?","k":1}' | python3 -c "import sys,json;print(len(json.load(sys.stdin).get('hits',[])))" 2>/dev/null)
[ "${hit:-0}" -ge 1 ] && ok "RAG ingest+query (hit)" || no "RAG query no hit"
rm -rf ~/.mostik-ai/u/smoke_rag 2>/dev/null

# 6. websearch (web+videos+images)
w=$(curl -s --max-time 25 -X POST $B/api/websearch -H 'content-type: application/json' -d '{"query":"electric cars 2026"}')
wn=$(echo "$w" | j "len(d.get('web',[]))"); vn=$(echo "$w" | j "len(d.get('videos',[]))"); im=$(echo "$w" | j "len(d.get('images',[]))")
[ "${wn:-0}" -ge 1 ] && ok "websearch web=$wn videos=$vn images=$im" || no "websearch empty"

# 7. browser open + screenshot + secret redaction is wired
br=$(curl -s --max-time 40 -X POST $B/api/browser -H 'content-type: application/json' -d '{"user":"smoke_b","action":"open","url":"https://example.com"}')
echo "$br" | python3 -c "import sys,json;d=json.load(sys.stdin);assert d.get('screenshot','').startswith('data:image');assert 'Example' in (d.get('text') or '')" 2>/dev/null \
  && ok "browser open+screenshot+text" || no "browser open failed"
curl -s -X POST $B/api/browser -H 'content-type: application/json' -d '{"user":"smoke_b","action":"close"}' >/dev/null

# 8. guard redaction (unit)
python3 -c "import guard;assert guard.redact_secrets('key sk-ABCD1234EFGH5678IJKL')!='key sk-ABCD1234EFGH5678IJKL'" 2>/dev/null \
  && ok "guard redacts secrets" || no "guard redaction broken"

echo "=== RESULT: $pass passed / $fail failed $(date +%H:%M:%S) ==="
exit $fail

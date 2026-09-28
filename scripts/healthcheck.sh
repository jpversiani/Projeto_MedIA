#!/usr/bin/env bash
# ============================================================
# MedIA Health OS — health check standalone
# Verifica: (1) /docs 200, (2) porta em LISTEN, (3) handshake
# WebSocket de telemedicina (rotas WS não constam no openapi.json
# do FastAPI, então testamos o upgrade real com curl).
# Uso: ./scripts/healthcheck.sh [PORT]   (padrão 8000)
# Exit code: 0 = saudável, 1 = degradado/falho
# ============================================================
set -euo pipefail

PORT="${1:-${PORT:-8000}}"
BASE="http://127.0.0.1:${PORT}"
falhas=0

log() { printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }

# 1) /docs
if curl -fsS -o /dev/null "${BASE}/docs"; then
  log "[OK] /docs respondeu 200 na porta ${PORT}."
else
  log "[FALHA] /docs nao respondeu na porta ${PORT}."
  falhas=$((falhas + 1))
fi

# 2) Porta em LISTEN
if command -v ss >/dev/null 2>&1 && ss -ltn "sport = :${PORT}" 2>/dev/null | grep -q LISTEN; then
  log "[OK] Porta ${PORT} em LISTEN."
else
  log "[FALHA] Porta ${PORT} nao esta em LISTEN."
  falhas=$((falhas + 1))
fi

# 3) Handshake WebSocket de telemedicina (esperado: HTTP 403/400 do
#    servidor indicando rota WS existente, ou 101 se autenticado).
#    Um 404 puro indicaria rota ausente.
ws_code="$(curl -s -o /dev/null -w '%{http_code}' \
  -H 'Connection: Upgrade' -H 'Upgrade: websocket' \
  -H 'Sec-WebSocket-Version: 13' -H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==' \
  "${BASE}/api/v1/ws/telemedicina/sala/healthcheck?paciente=paciente" || true)"
case "$ws_code" in
  101|403|400|426) log "[OK] Rota WS de telemedicina respondendo (HTTP ${ws_code})." ;;
  404|"") log "[FALHA] Rota WS de telemedicina ausente (HTTP ${ws_code:-sem resposta})."; falhas=$((falhas + 1)) ;;
  *) log "[DEGRADADO] Rota WS respondeu inesperadamente (HTTP ${ws_code})."; falhas=$((falhas + 1)) ;;
esac

if [ "$falhas" -eq 0 ]; then
  log "[SAUDAVEL] Todos os checks passaram."
  exit 0
else
  log "[NAO_SAUDAVEL] ${falhas} check(s) falharam."
  exit 1
fi
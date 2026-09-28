#!/usr/bin/env bash
# ============================================================
# MedIA Health OS — script de inicialização portável
# - BASE_DIR dinâmico (sem caminhos legados do Tabnet)
# - HOST/PORT parametrizáveis via variáveis de ambiente
# - Pré-checagem de porta ocupada (idempotente: se já há uvicorn
#   saudável na porta, apenas valida e sai; FORCE_RESTART=1 mata e sobe de novo)
# - Health check pós-start no /docs com timeout e falha explícita
# - Logs estruturados com timestamp; trap de limpeza em Ctrl+C/falha
# Uso:
#   ./start.sh                 # porta 8000
#   PORT=8010 ./start.sh       # sobe em outra porta (evita conflito com PID existente)
#   HOST=127.0.0.1 ./start.sh  # restringe interface
#   RELOAD=0 ./start.sh        # desativa --reload
#   FORCE_RESTART=1 ./start.sh # reinicia instância existente na porta
# ============================================================
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Parametrização ---
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
RELOAD="${RELOAD:-1}"
FORCE_RESTART="${FORCE_RESTART:-0}"
HEALTH_URL="http://127.0.0.1:${PORT}/docs"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-30}"

log() { printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }

# --- Ativação do .venv da raiz ---
if [ -f "$BASE_DIR/.venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "$BASE_DIR/.venv/bin/activate"
  log "[OK] venv ativado: $BASE_DIR/.venv"
else
  echo "[AVISO] Ambiente virtual nao encontrado em $BASE_DIR/.venv — usando Python do sistema." >&2
fi

command -v uvicorn >/dev/null 2>&1 || { echo "[ERRO] uvicorn nao encontrado no PATH." >&2; exit 1; }

# --- Pré-checagem de porta ocupada (idempotência/restart seguro) ---
if command -v ss >/dev/null 2>&1 && ss -ltn "sport = :${PORT}" 2>/dev/null | grep -q LISTEN; then
  ocupante="$(ss -ltnp "sport = :${PORT}" 2>/dev/null | grep -oP 'pid=\K[0-9]+' | head -1 || true)"
  if [ -n "${ocupante:-}" ] && ps -p "$ocupante" -o cmd= 2>/dev/null | grep -q uvicorn; then
    if [ "$FORCE_RESTART" = "1" ]; then
      log "[INFO] FORCE_RESTART=1 — encerrando uvicorn existente (PID ${ocupante}) na porta ${PORT}."
      kill "$ocupante" 2>/dev/null || true
      for _ in $(seq 1 10); do
        ss -ltn "sport = :${PORT}" 2>/dev/null | grep -q LISTEN || break
        sleep 0.5
      done
    else
      if curl -fsS -o /dev/null "http://127.0.0.1:${PORT}/docs" 2>/dev/null; then
        log "[OK] MedIA já em execução na porta ${PORT} (PID ${ocupante}) e saudável — nada a fazer."
        log "[INFO] Para reiniciar: FORCE_RESTART=1 ./start.sh | Para outra porta: PORT=8010 ./start.sh"
        exit 0
      else
        echo "[ERRO] Porta ${PORT} tem uvicorn (PID ${ocupante}) mas /docs nao responde. Rode: FORCE_RESTART=1 ./start.sh" >&2
        exit 1
      fi
    fi
  else
    echo "[ERRO] Porta ${PORT} ocupada por outro processo (PID ${ocupante:-desconhecido}). Use PORT=<outra> ./start.sh" >&2
    exit 1
  fi
fi

cd "$BASE_DIR/backend"

log "========================================================"
log " MedIA Health OS — e-SUS APS Open Source (PEC)"
log " Interface:  http://localhost:${PORT}"
log " API docs:   http://localhost:${PORT}/docs"
log "========================================================"

# --- Execução com trap de limpeza ---
UVICORN_PID=""
cleanup() {
  if [ -n "$UVICORN_PID" ] && kill -0 "$UVICORN_PID" 2>/dev/null; then
    log "[INFO] Encerrando uvicorn (PID ${UVICORN_PID})..."
    kill "$UVICORN_PID" 2>/dev/null || true
    wait "$UVICORN_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

RELOAD_FLAG=""
[ "$RELOAD" = "1" ] && RELOAD_FLAG="--reload"

# shellcheck disable=SC2086
uvicorn app.main:app --host "$HOST" --port "$PORT" $RELOAD_FLAG &
UVICORN_PID=$!

# --- Health check pós-start ---
log "[INFO] Aguardando health check em ${HEALTH_URL} (timeout ${HEALTH_TIMEOUT}s)..."
tentativa=0
while [ "$tentativa" -lt "$HEALTH_TIMEOUT" ]; do
  if ! kill -0 "$UVICORN_PID" 2>/dev/null; then
    echo "[ERRO] uvicorn morreu durante o startup." >&2
    exit 1
  fi
  if curl -fsS -o /dev/null "$HEALTH_URL" 2>/dev/null; then
    log "[OK] Health check passou: ${HEALTH_URL} respondeu 200."
    break
  fi
  tentativa=$((tentativa + 1))
  sleep 1
done
if [ "$tentativa" -ge "$HEALTH_TIMEOUT" ]; then
  echo "[ERRO] Health check falhou após ${HEALTH_TIMEOUT}s em ${HEALTH_URL}." >&2
  exit 1
fi

log "[INFO] Servidor pronto (PID ${UVICORN_PID}). Ctrl+C para encerrar."
wait "$UVICORN_PID"
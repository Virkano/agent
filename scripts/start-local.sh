#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -f ".env.local" ]; then
  echo "Missing .env.local" >&2
  exit 1
fi

set -a
source ".env.local"
set +a

export PATH="$ROOT_DIR/.venv/bin:$PATH"

mkdir -p \
  "$JB_LOG_DIR" \
  "$JB_TMPDIR" \
  "$JB_HF_HOME" \
  "$JB_TIKTOKEN_CACHE_DIR" \
  "$JB_CONFIG_DIR" \
  "$JB_EXTERNAL_LOCALE_PATH" \
  "$JB_EMBEDDING_MODEL_PATH" \
  "$JB_EMBEDDING_MODEL_NAME"

service="${1:-web}"

case "$service" in
  web)
    exec .venv/bin/python main.py dev web
    ;;
  celery)
    exec .venv/bin/python main.py dev celery
    ;;
  local_model)
    exec .venv/bin/python main.py dev local_model
    ;;
  admin-ui)
    exec pnpm --dir ui dev
    ;;
  chat-ui)
    exec pnpm --dir ui chat
    ;;
  migrate|upgrade_db)
    exec .venv/bin/python main.py upgrade_db
    ;;
  *)
    echo "Usage: scripts/start-local.sh [web|celery|local_model|admin-ui|chat-ui|migrate]" >&2
    exit 2
    ;;
esac

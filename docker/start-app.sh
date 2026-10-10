#!/usr/bin/env bash
set -euo pipefail

export PATH="/opt/venv/bin:${PATH}"

security_args=()
if [[ "${JB_DEPLOYMENT_MODE:-production}" == "production" ]]; then
  security_args+=(--production)
fi
python /opt/jb-agent-app/scripts/check-deployment-security.py "${security_args[@]}"

mkdir -p \
  "${JB_LOG_DIR:-/opt/jb-agent/logs}" \
  "${JB_TMPDIR:-/opt/jb-agent/tmp}" \
  "${JB_CONFIG_DIR:-/opt/jb-agent/conf}" \
  "${JB_EXTERNAL_LOCALE_PATH:-/opt/jb-agent/locales}" \
  /opt/jb-agent/python-packages

rm -rf "${JB_TMPDIR:-/opt/jb-agent/tmp:?}/"*
rm -f /opt/jb-agent-app/tmp/*.pid /opt/jb-agent-app/tmp/tool_executor_init_dir.lock 2>/dev/null || true

wait_for_tcp() {
  local name="$1"
  local host="$2"
  local port="$3"
  local timeout="${4:-120}"

  echo "Waiting for ${name} at ${host}:${port} ..."
  python - "$name" "$host" "$port" "$timeout" <<'PY'
import socket
import sys
import time

name, host, port, timeout = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
deadline = time.time() + timeout
last_error = None
while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=3):
            print(f"{name} is ready.")
            sys.exit(0)
    except OSError as exc:
        last_error = exc
        time.sleep(2)

print(f"Timed out waiting for {name} at {host}:{port}: {last_error}", file=sys.stderr)
sys.exit(1)
PY
}

wait_for_tcp "PostgreSQL" "${JB_DB_HOST:-host.docker.internal}" "${JB_DB_PORT:-5432}" 120
wait_for_tcp "Redis" "${JB_REDIS_HOST:-host.docker.internal}" "${JB_REDIS_PORT:-6379}" 60

if [[ "${JB_START_LOCAL_MODEL:-true}" == "true" ]]; then
  echo "Embedded vector service will listen inside the container at ${JB_LOCAL_MODEL_HOST:-127.0.0.1}:${JB_LOCAL_MODEL_PORT:-11636}."
fi

cd /opt/jb-agent-app
/opt/venv/bin/python main.py start web task

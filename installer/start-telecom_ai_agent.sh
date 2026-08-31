#!/bin/bash

if [ ! -d /opt/telecom_ai_agent/logs ]; then
    mkdir -p /opt/telecom_ai_agent/logs
fi
chmod -R 700 /opt/telecom_ai_agent/logs
if [ ! -d /opt/telecom_ai_agent/local ]; then
    mkdir -p /opt/telecom_ai_agent/local
    chmod 700 /opt/telecom_ai_agent/local
fi
mkdir -p /opt/telecom_ai_agent/python-packages

rm -f /opt/telecom_ai_agent-app/tmp/*

_INIT_SHELL_DIR=${TELECOM_AI_INIT_SHELL_DIR:-/opt/telecom_ai_agent/local/init-shells}
if [ -d $_INIT_SHELL_DIR ]; then
    chmod -R g-rwx $_INIT_SHELL_DIR
    find $_INIT_SHELL_DIR -maxdepth 1 -type f -name "*.sh" | sort | while IFS= read -r f; do
        if bash "$f"; then
            echo "[OK] init-shell >>> $f"
        else
            echo "[ERROR] init-shell >>> $f failed with exit code $?" >&2
        fi
    done
fi

python /opt/telecom_ai_agent-app/main.py start
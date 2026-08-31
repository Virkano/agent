#!/bin/bash

set -e

if [ -f "/opt/telecom_ai_agent/PG_VERSION" ] || [ -f "/var/lib/postgresql/data/PG_VERSION" ]; then
  # 如果是v1版本一键安装的的目录则退出
  echo -e "\033[1;31mFATAL ERROR: Upgrade from v1 to v2 is not supported.\033[0m"
  echo -e "\033[1;31mThe process will exit.\033[0m"
  exit 1
fi

if [ "$TELECOM_AI_DB_HOST" = "127.0.0.1" ]; then
  echo -e "\033[1;32mPostgreSQL starting...\033[0m"
  /usr/bin/start-postgres.sh &
  postgres_pid=$!
  sleep 5
  wait-for-it 127.0.0.1:5432 --timeout=120 --strict -- echo -e "\033[1;32mPostgreSQL started.\033[0m"
fi

if [ "$TELECOM_AI_REDIS_HOST" = "127.0.0.1" ]; then
  echo -e "\033[1;32mRedis starting...\033[0m"
  /usr/bin/start-redis.sh &
  redis_pid=$!
  sleep 5
  wait-for-it 127.0.0.1:6379 --timeout=60 --strict -- echo -e "\033[1;32mRedis started.\033[0m"
fi

echo -e "\033[1;32mTelecom AI Agent starting...\033[0m"
/usr/bin/start-telecom_ai_agent.sh &
telecom_ai_pid=$!
sleep 10
wait-for-it 127.0.0.1:8080 --timeout=180 --strict -- echo -e "\033[1;32mTelecom AI Agent started.\033[0m"

wait -n
echo -e "\033[1;31mSystem is shutting down.\033[0m"
kill $postgres_pid $redis_pid $telecom_ai_pid 2>/dev/null
wait

#!/bin/bash

if [ ! -d /opt/telecom_ai_agent/data/redis ]; then
    mkdir -p /opt/telecom_ai_agent/data/redis
    chmod 700 /opt/telecom_ai_agent/data/redis
fi
if [ ! -d /opt/telecom_ai_agent/logs ]; then
    mkdir -p /opt/telecom_ai_agent/logs
    chmod 700 /opt/telecom_ai_agent/logs
fi
if [ ! -f /opt/telecom_ai_agent/conf/redis.conf ]; then
  mkdir -p /opt/telecom_ai_agent/conf
  touch /opt/telecom_ai_agent/conf/redis.conf
  chmod 700 /opt/telecom_ai_agent/conf/redis.conf
  cat <<EOF > /opt/telecom_ai_agent/conf/redis.conf
bind 0.0.0.0
port 6379
databases 16
maxmemory 1G
aof-use-rdb-preamble yes
save 30 1
save 10 10
save 5 20
dbfilename dump.rdb
rdbcompression yes
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
maxmemory-policy allkeys-lru
loglevel warning
logfile /opt/telecom_ai_agent/logs/redis.log
dir /opt/telecom_ai_agent/data/redis
requirepass ${REDIS_PASSWORD}
EOF
fi

redis-server /opt/telecom_ai_agent/conf/redis.conf
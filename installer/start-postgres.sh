#!/bin/bash

mkdir -p /opt/telecom_ai_agent/data/postgresql
docker-entrypoint.sh postgres -c max_connections=${POSTGRES_MAX_CONNECTIONS} -c jit=off

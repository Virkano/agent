FROM node:24-alpine AS web-build

WORKDIR /build/ui
COPY ui/package.json ui/pnpm-lock.yaml ./
RUN corepack enable && \
    corepack prepare pnpm@10.28.2 --activate && \
    pnpm install --frozen-lockfile --config.dangerously-allow-all-builds=true
COPY ui ./
RUN NODE_OPTIONS="--max-old-space-size=4096" pnpm run build && \
    NODE_OPTIONS="--max-old-space-size=4096" pnpm run build-chat

FROM python:3.11-slim-bookworm AS python-build

ARG APT_DEBIAN_MIRROR=http://mirrors.aliyun.com/debian
ARG APT_SECURITY_MIRROR=http://mirrors.aliyun.com/debian-security

ENV PYTHONUNBUFFERED=1 \
    PATH=/opt/venv/bin:$PATH \
    JB_CONFIG_TYPE=ENV \
    JB_DB_NAME=initdb \
    JB_DB_HOST=host.docker.internal \
    JB_DB_PORT=5432 \
    JB_DB_USER=root \
    JB_DB_PASSWORD=123456 \
    JB_REDIS_HOST=host.docker.internal \
    JB_REDIS_PORT=6379 \
    JB_REDIS_DB=0 \
    JB_REDIS_PASSWORD="" \
    JB_ADMIN_PATH=/admin \
    JB_CHAT_PATH=/chat \
    JB_LOG_DIR=/opt/jb-agent/logs \
    JB_TMPDIR=/opt/jb-agent/tmp \
    JB_CONFIG_DIR=/opt/jb-agent/conf \
    JB_EXTERNAL_LOCALE_PATH=/opt/jb-agent/locales \
    JB_HF_HOME=/opt/jb-agent-app/model/base \
    JB_TOKENIZER_MODEL_PATH=/opt/jb-agent-app/model/tokenizer/models--bert-base-cased \
    JB_TIKTOKEN_CACHE_DIR=/opt/jb-agent-app/model/tokenizer/openai-tiktoken-cl100k-base \
    JB_EMBEDDING_MODEL_PATH=/opt/jb-agent-app/model/embedding \
    JB_EMBEDDING_MODEL_NAME=telecom-ai-local-hash-embedding \
    JB_SANDBOX_HOME=/opt/jb-agent-app/sandbox

WORKDIR /opt/jb-agent-app
COPY . /opt/jb-agent-app
COPY --from=web-build /build/ui/dist /opt/jb-agent-app/ui/dist

RUN set -eux; \
    sed -i \
      -e "s|http://deb.debian.org/debian-security|${APT_SECURITY_MIRROR}|g" \
      -e "s|http://security.debian.org/debian-security|${APT_SECURITY_MIRROR}|g" \
      -e "s|http://deb.debian.org/debian|${APT_DEBIAN_MIRROR}|g" \
      /etc/apt/sources.list /etc/apt/sources.list.d/* 2>/dev/null || true; \
    printf 'Acquire::Retries "5";\nAcquire::http::Timeout "30";\nAcquire::https::Timeout "30";\n' > /etc/apt/apt.conf.d/80-retries; \
    apt-get update && \
    apt-get install -y --no-install-recommends build-essential gcc g++ gettext libexpat1-dev libffi-dev curl ca-certificates && \
    apt-get clean all && \
    rm -rf /var/lib/apt/lists/* && \
    python -m venv /opt/venv && \
    mkdir -p ${JB_SANDBOX_HOME}/lib /opt/jb-agent-app/model/tokenizer && \
    gcc -shared -fPIC -o ${JB_SANDBOX_HOME}/lib/sandbox.so /opt/jb-agent-app/installer/sandbox.c -ldl && \
    pip install --no-cache-dir uv && \
    python -m uv pip install -r pyproject.toml && \
    python -c "from transformers import BertTokenizer; BertTokenizer.from_pretrained('bert-base-cased', cache_dir='/opt/jb-agent-app/model/tokenizer')" && \
    python /opt/jb-agent-app/apps/manage.py compilemessages && \
    export PIP_TARGET=/opt/jb-agent-app/sandbox/python-packages && \
    python -m uv pip install --target=$PIP_TARGET requests pymysql psycopg2-binary && \
    rm -rf /opt/jb-agent-app/ui/node_modules /opt/jb-agent-app/.git /opt/jb-agent-app/.venv

FROM python:3.11-slim-bookworm

ARG APT_DEBIAN_MIRROR=http://mirrors.aliyun.com/debian
ARG APT_SECURITY_MIRROR=http://mirrors.aliyun.com/debian-security
ARG DOCKER_IMAGE_TAG=local
ARG BUILD_AT
ARG GITHUB_COMMIT

ENV PYTHONUNBUFFERED=1 \
    PATH=/opt/venv/bin:$PATH \
    JB_VERSION="${DOCKER_IMAGE_TAG} (build at ${BUILD_AT}, commit: ${GITHUB_COMMIT})" \
    JB_CONFIG_TYPE=ENV \
    JB_ADMIN_PATH=/admin \
    JB_CHAT_PATH=/chat \
    JB_LOG_LEVEL=INFO \
    JB_DB_NAME=initdb \
    JB_DB_HOST=host.docker.internal \
    JB_DB_PORT=5432 \
    JB_DB_USER=root \
    JB_DB_PASSWORD=123456 \
    JB_DB_MAX_OVERFLOW=80 \
    JB_REDIS_HOST=host.docker.internal \
    JB_REDIS_PORT=6379 \
    JB_REDIS_DB=0 \
    JB_REDIS_PASSWORD="" \
    JB_REDIS_MAX_CONNECTIONS=100 \
    JB_LOG_DIR=/opt/jb-agent/logs \
    JB_TMPDIR=/opt/jb-agent/tmp \
    JB_CONFIG_DIR=/opt/jb-agent/conf \
    JB_EXTERNAL_LOCALE_PATH=/opt/jb-agent/locales \
    JB_HF_HOME=/opt/jb-agent-app/model/base \
    JB_TOKENIZER_MODEL_PATH=/opt/jb-agent-app/model/tokenizer/models--bert-base-cased \
    JB_TIKTOKEN_CACHE_DIR=/opt/jb-agent-app/model/tokenizer/openai-tiktoken-cl100k-base \
    JB_EMBEDDING_MODEL_PATH=/opt/jb-agent-app/model/embedding \
    JB_EMBEDDING_MODEL_NAME=telecom-ai-local-hash-embedding \
    JB_SANDBOX=1 \
    JB_SANDBOX_HOME=/opt/jb-agent-app/sandbox \
    JB_SANDBOX_PYTHON_PACKAGE_PATHS="/opt/venv/lib/python3.11/site-packages,/opt/jb-agent-app/sandbox/python-packages,/opt/jb-agent/python-packages" \
    JB_SANDBOX_PYTHON_BANNED_HOSTS="127.0.0.0/8,localhost,host.docker.internal,172.17.0.0/16,telecom_ai_agent,pgsql,redis,172.31.250.192/26,0.0.0.0/32,::/0" \
    PIP_TARGET=/opt/jb-agent/python-packages

RUN set -eux; \
    sed -i \
      -e "s|http://deb.debian.org/debian-security|${APT_SECURITY_MIRROR}|g" \
      -e "s|http://security.debian.org/debian-security|${APT_SECURITY_MIRROR}|g" \
      -e "s|http://deb.debian.org/debian|${APT_DEBIAN_MIRROR}|g" \
      /etc/apt/sources.list /etc/apt/sources.list.d/* 2>/dev/null || true; \
    printf 'Acquire::Retries "5";\nAcquire::http::Timeout "30";\nAcquire::https::Timeout "30";\n' > /etc/apt/apt.conf.d/80-retries; \
    apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates ffmpeg && \
    apt-get clean all && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/jb-agent-app
COPY --from=python-build /opt/jb-agent-app /opt/jb-agent-app
COPY --from=python-build /opt/venv /opt/venv
COPY --chmod=755 docker/start-app.sh /usr/local/bin/start-app.sh

EXPOSE 8080
VOLUME /opt/jb-agent

ENTRYPOINT ["/usr/local/bin/start-app.sh"]

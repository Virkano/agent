FROM node:24-alpine AS web-build
COPY ui ui
RUN cd ui && ls -la && if [ -d "dist" ]; then exit 0; fi && \
    npm install --prefer-offline --no-audit && \
    npm install -D concurrently && \
    NODE_OPTIONS="--max-old-space-size=4096" npx concurrently "npm run build" "npm run build-chat" && \
    find . -maxdepth 1 ! -name '.' ! -name 'dist' ! -name 'public' -exec rm -rf {} +

FROM ghcr.io/1panel-dev/telecom_ai_agent-base:python3.11-pg17.10-20260525 AS stage-build
COPY --chmod=700 . /opt/telecom_ai_agent-app
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ gettext libexpat1-dev libffi-dev && \
    apt-get clean all  && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /opt/telecom_ai_agent-app
RUN gcc -shared -fPIC -o ${TELECOM_AI_SANDBOX_HOME}/lib/sandbox.so /opt/telecom_ai_agent-app/installer/sandbox.c -ldl && \
    rm -rf /opt/telecom_ai_agent-app/ui && \
    pip install uv --break-system-packages && \
    python -m uv pip install -r pyproject.toml && \
    find /opt/telecom_ai_agent-app  -depth \( -name ".git*" -o -name ".docker*" -o -name ".idea*" -o -name ".editorconfig*" -o -name ".prettierrc*" -o -name "README.md" -o -name "poetry.lock" -o -name "pyproject.toml"  \) -exec rm -rf {} + && \
    python /opt/telecom_ai_agent-app/apps/manage.py compilemessages && \
    export PIP_TARGET=/opt/telecom_ai_agent-app/sandbox/python-packages && \
    python -m uv pip install --target=$PIP_TARGET requests pymysql psycopg2-binary && \
    rm -rf /opt/telecom_ai_agent-app/installer
COPY --from=web-build --chmod=700 ui /opt/telecom_ai_agent-app/ui

FROM ghcr.io/1panel-dev/telecom_ai_agent-base:python3.11-pg17.10-20260525
ARG DOCKER_IMAGE_TAG=dev \
    BUILD_AT \
    GITHUB_COMMIT

ENV TELECOM_AI_VERSION="${DOCKER_IMAGE_TAG} (build at ${BUILD_AT}, commit: ${GITHUB_COMMIT})" \
    TELECOM_AI_DB_NAME=telecom_ai_agent \
    TELECOM_AI_DB_HOST=127.0.0.1 \
    TELECOM_AI_DB_PORT=5432  \
    TELECOM_AI_DB_USER=${POSTGRES_USER} \
    TELECOM_AI_DB_PASSWORD=${POSTGRES_PASSWORD} \
    TELECOM_AI_DB_MAX_OVERFLOW=80 \
    TELECOM_AI_REDIS_HOST=127.0.0.1 \
    TELECOM_AI_REDIS_PORT=6379 \
    TELECOM_AI_REDIS_DB=0 \
    TELECOM_AI_REDIS_PASSWORD=${REDIS_PASSWORD} \
    TELECOM_AI_EMBEDDING_MODEL_PATH=/opt/telecom_ai_agent-app/model/embedding \
    TELECOM_AI_EMBEDDING_MODEL_NAME=/opt/telecom_ai_agent-app/model/embedding/shibing624_text2vec-base-chinese \
    TELECOM_AI_LOCAL_MODEL_HOST=127.0.0.1 \
    TELECOM_AI_LOCAL_MODEL_PORT=11636 \
    TELECOM_AI_LOCAL_MODEL_PROTOCOL=http \
    PIP_TARGET=/opt/telecom_ai_agent/python-packages

WORKDIR /opt/telecom_ai_agent-app
COPY --from=stage-build /opt/telecom_ai_agent-app /opt/telecom_ai_agent-app
COPY --from=stage-build /opt/py3 /opt/py3

EXPOSE 8080
VOLUME /opt/telecom_ai_agent
ENTRYPOINT ["bash", "-c"]
CMD [ "/usr/bin/start-all.sh" ]
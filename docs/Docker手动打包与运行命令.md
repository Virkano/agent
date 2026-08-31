# Docker 手动打包与运行命令

本文档用于后续手动打包和启动当前项目。当前建议方案是：

- PostgreSQL 外部部署，不打进应用镜像
- Redis 外部部署，不打进应用镜像
- Ollama 外部部署，通过接口地址配置，不打进应用镜像
- 应用镜像包含后端服务和已构建的管理端、聊天端静态资源

## 1. 本地检查

```bash
cd <project-dir>
git status --short
docker version
docker info
```

## 2. 可选：创建 Docker 网络

如果 PostgreSQL、Redis、应用容器都用 Docker 跑，建议放到同一个网络。

```bash
docker network create jb-agent-net
```

如果网络已存在，会提示已存在，忽略即可。

## 3. 启动 PostgreSQL

首次启动：

```bash
docker run -d \
  --name jb-postgres \
  --network jb-agent-net \
  -e POSTGRES_DB=telecom_ai_agent \
  -e POSTGRES_USER=root \
  -e POSTGRES_PASSWORD=123456 \
  -p 5432:5432 \
  -v jb-postgres-data:/var/lib/postgresql/data \
  pgvector/pgvector:pg17
```

后续启动：

```bash
docker start jb-postgres
```

检查：

```bash
docker ps --filter name=jb-postgres
docker logs --tail=100 jb-postgres
```

## 4. 启动 Redis

当前本地 Redis 无密码。

首次启动：

```bash
docker run -d \
  --name jb-redis \
  --network jb-agent-net \
  -p 6379:6379 \
  -v jb-redis-data:/data \
  redis:7-alpine \
  redis-server --appendonly yes
```

后续启动：

```bash
docker start jb-redis
```

检查：

```bash
docker ps --filter name=jb-redis
docker logs --tail=100 jb-redis
```

## 5. 构建应用镜像

使用应用专用 Dockerfile 打包。这个 Dockerfile 只打应用，不启动内置 PostgreSQL、Redis、Ollama。

```bash
cd <project-dir>

docker build \
  -f docker/Dockerfile.app \
  -t jb-agent:slim-local \
  --build-arg DOCKER_IMAGE_TAG=local \
  --build-arg BUILD_AT="$(date '+%Y-%m-%d %H:%M:%S')" \
  --build-arg GITHUB_COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo local)" \
  .
```

查看镜像：

```bash
docker images | grep jb-agent
```

## 6. 运行应用容器：连接同 Docker 网络里的 PostgreSQL/Redis

这种方式适合第 3、4 步的 `jb-postgres`、`jb-redis`。

```bash
docker run -d \
  --name jb-agent-app \
  --network jb-agent-net \
  -p 8080:8080 \
  -e JB_CONFIG_TYPE=ENV \
  -e JB_DB_NAME=initdb \
  -e JB_DB_HOST=jb-postgres \
  -e JB_DB_PORT=5432 \
  -e JB_DB_USER=root \
  -e JB_DB_PASSWORD=123456 \
  -e JB_DB_MAX_OVERFLOW=80 \
  -e JB_REDIS_HOST=jb-redis \
  -e JB_REDIS_PORT=6379 \
  -e JB_REDIS_DB=0 \
  -e JB_REDIS_PASSWORD= \
  -e JB_REDIS_MAX_CONNECTIONS=100 \
  -e JB_ADMIN_PATH=/admin \
  -e JB_CHAT_PATH=/chat \
  -e JB_LOG_LEVEL=INFO \
  -v jb-agent-data:/opt/jb-agent \
  jb-agent:slim-local
```

## 7. 运行应用容器：连接宿主机已有 PostgreSQL/Redis

Mac 本地 Docker 访问宿主机服务一般使用 `host.docker.internal`。

```bash
docker run -d \
  --name jb-agent-app \
  -p 8080:8080 \
  -e JB_CONFIG_TYPE=ENV \
  -e JB_DB_NAME=initdb \
  -e JB_DB_HOST=host.docker.internal \
  -e JB_DB_PORT=5432 \
  -e JB_DB_USER=root \
  -e JB_DB_PASSWORD=123456 \
  -e JB_DB_MAX_OVERFLOW=80 \
  -e JB_REDIS_HOST=host.docker.internal \
  -e JB_REDIS_PORT=6379 \
  -e JB_REDIS_DB=0 \
  -e JB_REDIS_PASSWORD= \
  -e JB_REDIS_MAX_CONNECTIONS=100 \
  -e JB_ADMIN_PATH=/admin \
  -e JB_CHAT_PATH=/chat \
  -e JB_LOG_LEVEL=INFO \
  -v jb-agent-data:/opt/jb-agent \
  jb-agent:slim-local
```

## 8. 访问地址

应用镜像里管理端和聊天端都由后端统一服务提供：

```text
http://localhost:8080/admin
http://localhost:8080/chat
http://localhost:8080/admin/api-doc/
```

本地开发环境里的 `3000` 是 Vite 开发服务端口；Docker 镜像运行时默认只暴露 `8080`。

## 9. 查看日志和状态

```bash
docker ps --filter name=jb-agent-app
docker logs -f --tail=200 jb-agent-app
```

进入容器：

```bash
docker exec -it jb-agent-app bash
```

容器内查看服务日志：

```bash
ls -lah /opt/jb-agent/logs
tail -f /opt/jb-agent/logs/gunicorn.log
tail -f /opt/jb-agent/logs/celery_default.log
```

## 10. 停止、删除、重启

停止应用：

```bash
docker stop jb-agent-app
```

重新启动应用：

```bash
docker start jb-agent-app
```

删除应用容器：

```bash
docker rm -f jb-agent-app
```

删除镜像：

```bash
docker rmi jb-agent:slim-local
```

## 11. 重新打包并替换运行

```bash
docker rm -f jb-agent-app

docker build \
  -f docker/Dockerfile.app \
  -t jb-agent:slim-local \
  --build-arg DOCKER_IMAGE_TAG=local \
  --build-arg BUILD_AT="$(date '+%Y-%m-%d %H:%M:%S')" \
  --build-arg GITHUB_COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo local)" \
  .

docker run -d \
  --name jb-agent-app \
  --network jb-agent-net \
  -p 8080:8080 \
  -e JB_CONFIG_TYPE=ENV \
  -e JB_DB_NAME=initdb \
  -e JB_DB_HOST=jb-postgres \
  -e JB_DB_PORT=5432 \
  -e JB_DB_USER=root \
  -e JB_DB_PASSWORD=123456 \
  -e JB_REDIS_HOST=jb-redis \
  -e JB_REDIS_PORT=6379 \
  -e JB_REDIS_DB=0 \
  -e JB_REDIS_PASSWORD= \
  -e JB_ADMIN_PATH=/admin \
  -e JB_CHAT_PATH=/chat \
  -v jb-agent-data:/opt/jb-agent \
  jb-agent:slim-local
```

## 12. Ollama 配置说明

Ollama 暂时不打包进应用镜像。服务器上单独部署 Ollama 后，在系统的私有模型配置中填写 Ollama 地址即可。

如果应用容器访问宿主机 Ollama：

```text
http://host.docker.internal:11434
```

如果应用容器和 Ollama 在同一个 Docker 网络：

```text
http://ollama:11434
```

如果 Ollama 在独立服务器：

```text
http://服务器IP:11434
```

## 13. 常见检查命令

检查数据库连通：

```bash
docker exec -it jb-postgres psql -U root -d telecom_ai_agent -c '\dt'
```

检查 Redis 连通：

```bash
docker exec -it jb-redis redis-cli ping
```

检查应用接口：

```bash
curl -i http://localhost:8080/admin/api/profile
```

检查管理端页面：

```bash
curl -I http://localhost:8080/admin/
```

检查聊天端页面：

```bash
curl -I http://localhost:8080/chat/
```

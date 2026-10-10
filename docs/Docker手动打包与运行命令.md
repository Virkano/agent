# 单业务镜像构建与运行

## 1. 部署边界

项目只交付一个业务镜像 `telecom-ai-agent`：

- 镜像内包含管理端、聊天端、Django、Celery 和本地向量服务；
- 镜像只对外暴露 HTTP `8080`；
- 本地向量服务只监听容器内 `127.0.0.1:11636`，不对宿主机暴露；
- PostgreSQL、Redis 使用部署环境中已有的实例，通过环境变量连接；
- Ollama 不进入镜像，通过 `JB_OLLAMA_BASE_URL` 连接宿主机或独立服务器。

根目录 `docker-compose.yml` 只定义业务容器，不会创建、拉取或删除 PostgreSQL/Redis 镜像和数据卷。

## 2. 数据库初始化

仓库提供不含业务数据和凭证的安全初始化脚本。使用 PostgreSQL 管理账号执行：

```bash
psql -h <postgres-host> -p 5432 -U <admin-user> -d postgres \
  -v app_db=initdb -f docker/initdb.sql
```

脚本默认创建 `initdb`，也可通过 `app_db` 指定其他数据库名；数据库已存在时不会删除或覆盖，只会确认并启用 `vector` 扩展。随后启动业务镜像，启动程序会自动执行 Django migrations，创建全部业务表并升级到当前代码对应的最新结构。

初始化脚本不创建数据库账号。执行脚本的管理员应提前创建业务账号，并确保 `JB_DB_USER` 对目标数据库拥有连接、建表、序列和读写权限。仓库不提供默认生产数据、验收数据、管理员口令、Token 或模型密钥。

初始化 SQL 被 `.dockerignore` 排除，不会进入业务镜像。

## 3. 配置外部服务

```bash
cp docker/.env.example docker/.env
```

修改 `docker/.env` 中的 PostgreSQL、Redis 和 Ollama 地址。Mac/Windows 上，容器访问宿主机通常使用 `host.docker.internal`；Linux 的 Compose 配置已添加 `host-gateway` 映射。

最关键的配置：

```dotenv
JB_DB_NAME=initdb
JB_DB_HOST=host.docker.internal
JB_DB_PORT=5432
JB_DB_USER=root
JB_DB_PASSWORD=<数据库口令>

JB_REDIS_HOST=host.docker.internal
JB_REDIS_PORT=6379
JB_REDIS_DB=0
JB_REDIS_PASSWORD=<Redis 口令，无密码时留空>

JB_OLLAMA_BASE_URL=http://host.docker.internal:11434
```

`docker/.env` 已加入 Git 忽略规则，不要提交真实口令。

## 4. 构建镜像

推荐命令：

```bash
docker compose --env-file docker/.env build app
```

也可以直接构建：

```bash
docker build \
  -f docker/Dockerfile.app \
  -t telecom-ai-agent:local \
  --build-arg DOCKER_IMAGE_TAG=local \
  --build-arg BUILD_AT="$(date '+%Y-%m-%d %H:%M:%S')" \
  --build-arg GITHUB_COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo local)" \
  .
```

构建完成后应只需要分发：

```text
telecom-ai-agent:local
```

如需离线交付，只导出这一个业务镜像：

```bash
docker save -o telecom-ai-agent-local.tar telecom-ai-agent:local
```

目标环境导入：

```bash
docker load -i telecom-ai-agent-local.tar
```

PostgreSQL 和 Redis 镜像不在该 tar 包中。

## 5. 运行

```bash
docker compose --env-file docker/.env up -d --no-build app
docker compose --env-file docker/.env ps
```

直接运行镜像时，建议使用 env 文件，避免口令出现在命令历史：

```bash
docker run -d \
  --name telecom-ai-agent \
  --init \
  --restart unless-stopped \
  --add-host host.docker.internal:host-gateway \
  --env-file docker/.env \
  -p 8080:8080 \
  -v telecom-ai-agent-data:/opt/jb-agent \
  telecom-ai-agent:local
```

访问地址：

```text
管理端：http://localhost:8080/admin/
聊天端：http://localhost:8080/chat/
健康检查：http://localhost:8080/healthz
接口文档：http://localhost:8080/admin/api-doc/
```

## 6. 健康检查与验收

`/healthz` 同时验证 PostgreSQL 查询、Redis 读写和容器内向量服务端口。任一依赖异常都会返回 503。

```bash
curl -fsS http://127.0.0.1:8080/healthz
docker logs --tail=200 telecom-ai-agent
docker exec telecom-ai-agent sh -c 'test -n "$(command -v gunicorn)"'
```

还应确认：

- `docker inspect telecom-ai-agent` 只有 `8080/tcp` 暴露声明；
- 容器内 `127.0.0.1:11636` 可连接，但宿主机没有对应端口映射；
- 未认证管理 API 返回 401 而不是 500；
- 容器能访问配置的 Ollama `/api/tags`；
- 日志中没有数据库口令、Redis 口令或模型凭证。

## 7. 生产配置

切换为生产模式前必须设置：

```dotenv
JB_DEPLOYMENT_MODE=production
JB_SECRET_KEY=<至少 32 位随机密钥>
JB_ALLOWED_HOSTS=<正式域名>
JB_HEALTHCHECK_HOST=<正式域名>
JB_DB_PASSWORD=<数据库强口令>
JB_REDIS_PASSWORD=<Redis 强口令>
JB_DEFAULT_PASSWORD=<首次登录强口令>
```

生产 HTTPS 由反向代理、Ingress 或云平台负载均衡终止。启动脚本会先执行安全门禁，生产必填项缺失、默认口令、通配域名或 DEBUG 开启时会拒绝启动。

## 8. 常见故障

### 数据库端口可访问但应用仍启动失败

端口开放不代表 PostgreSQL 已能执行查询。检查目标数据库是否存在、账号权限、vector 扩展和 migrations 日志。

### 本地向量服务异常

查看容器内 `/opt/jb-agent/logs/local_model.log`。根路径 404 不能作为离线判断，应使用数据库中模型 UUID 调用真实 `embed_query` 接口。

### Ollama 无法连接

先在 Ollama 所在主机调用 `GET /api/tags`，再确认 `JB_OLLAMA_BASE_URL` 对容器可达。数据库中原来保存为 `127.0.0.1` 的 Ollama 地址可由该运行时配置覆盖。

### Docker Desktop 拉取或构建反复中断

先执行 `docker info`。如果全局配置了大量失效的 registry mirror，镜像层可能不断重试；这属于 Docker 守护进程/镜像代理问题，不是业务代码错误。

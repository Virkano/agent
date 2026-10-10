# 线上营销智能体平台

面向线上营销、知识库问答、智能体编排、运营监控、风险预警和故障预演的一体化智能体平台。

当前仓库按“一个业务镜像 + 外部基础设施”交付：业务镜像包含管理端、聊天端、Django、Celery 和本地向量服务，只对外暴露 `8080`；PostgreSQL、Redis 和 Ollama 由部署环境独立提供。

## 快速启动

### 1. 准备依赖

启动前确认以下服务可用：

- Docker Engine 和 Docker Compose v2；
- PostgreSQL，并已安装 `pgvector` 扩展；
- Redis；
- Ollama，或可访问的兼容 Ollama HTTPS 服务。

PostgreSQL、Redis 不包含在本仓库的 Compose 文件中，也不会被业务容器创建或删除。

### 2. 初始化数据库

在仓库根目录执行：

```bash
psql -h <postgres-host> -p 5432 -U <admin-user> -d postgres \
  -v app_db=initdb \
  -f docker/initdb.sql
```

该脚本可重复执行，只创建目标数据库并启用 `pgvector`，不导入本地数据或凭证。业务容器首次启动时会自动执行 Django migrations，创建全部业务表。

### 3. 配置运行环境

```bash
cp docker/.env.example docker/.env
```

至少检查并修改以下配置：

```dotenv
JB_DB_NAME=initdb
JB_DB_HOST=host.docker.internal
JB_DB_PORT=5432
JB_DB_USER=root
JB_DB_PASSWORD=<数据库密码>

JB_REDIS_HOST=host.docker.internal
JB_REDIS_PORT=6379
JB_REDIS_DB=0
JB_REDIS_PASSWORD=<Redis密码，无密码时本地模式可留空>

JB_OLLAMA_BASE_URL=http://host.docker.internal:11434
```

Mac、Windows，以及使用本仓库 Compose 配置的 Linux 环境，可通过 `host.docker.internal` 访问宿主机端口。Ollama 位于远程服务器时，可直接填写 `https://模型服务域名`，不要追加 `/api`。

`docker/.env` 已被 Git 忽略，请勿把真实口令或密钥提交到仓库。

### 4. 构建并启动

```bash
docker compose --env-file docker/.env config
docker compose --env-file docker/.env build app
docker compose --env-file docker/.env up -d --no-build app
```

查看运行状态：

```bash
docker compose --env-file docker/.env ps
docker compose --env-file docker/.env logs --tail=200 app
curl -fsS http://127.0.0.1:8080/healthz
```

健康检查返回 `{"status":"ok"}` 后访问：

- 管理端：<http://localhost:8080/admin/>
- 聊天端：<http://localhost:8080/chat/>
- API 文档：<http://localhost:8080/admin/api-doc/>
- 健康检查：<http://localhost:8080/healthz>

全新数据库的管理员用户名为 `admin`，初始密码取数据库第一次迁移时的 `JB_DEFAULT_PASSWORD`。首次登录后应立即修改密码。

### 5. 停止和重启

```bash
# 重启业务容器
docker compose --env-file docker/.env restart app

# 停止并移除业务容器；不会删除 PostgreSQL、Redis 或业务数据卷
docker compose --env-file docker/.env down
```

Docker 镜像本身不能“停止”，需要停止的是使用该镜像创建的容器。不要在需要保留运行数据时执行 `docker compose down -v`。

## 生产部署提示

生产环境必须把 `JB_DEPLOYMENT_MODE` 设置为 `production`，配置独立的密钥、强口令和明确域名，并在可信反向代理或 Ingress 上终止 HTTPS：

```dotenv
JB_DEPLOYMENT_MODE=production
JB_SECRET_KEY=<至少32位的独立随机密钥>
JB_ALLOWED_HOSTS=agent.example.com
JB_HEALTHCHECK_HOST=agent.example.com
JB_DB_PASSWORD=<数据库强口令>
JB_REDIS_PASSWORD=<Redis强口令>
JB_DEFAULT_PASSWORD=<首次登录强口令>
```

生产配置不满足安全门禁时，容器会拒绝启动。完整交付步骤、离线镜像、验收清单和故障排查见 [项目交付与运行手册](docs/项目交付与运行手册.md)。

## 项目文档

- [全功能演讲与演示串讲稿](docs/全功能演讲与演示串讲稿.md)
- [按角色分批演示手册](docs/演示角色稿/README.md)
- [项目交付与运行手册](docs/项目交付与运行手册.md)
- [Docker 手动打包与运行命令](docs/Docker手动打包与运行命令.md)
- [项目目录说明](docs/项目目录说明.md)
- [开发与运维排障手册](docs/开发与运维排障手册.md)
- [建设方案全量粗粒度 V1 实施计划](docs/建设方案全量粗粒度V1实施计划.md)

## 技术栈

- 前端：Vue 3、TypeScript、Vite
- 后端：Python 3.11、Django、Django REST Framework、Celery
- 智能体：LangChain、Ollama
- 数据库：PostgreSQL、pgvector
- 缓存：Redis
- 部署：Docker、Docker Compose

## License

Licensed under The GNU General Public License version 3 (GPLv3) (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

<https://www.gnu.org/licenses/gpl-3.0.html>

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

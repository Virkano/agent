-- 线上营销智能体平台 PostgreSQL 安全初始化脚本
--
-- 用途：
--   1. 创建业务数据库（不存在时）；
--   2. 在业务数据库中启用 pgvector 扩展；
--   3. 不导入本地验收数据、账号、口令、Token 或模型密钥。
--
-- 默认数据库名为 initdb，可通过 psql 变量覆盖：
--   psql -h <host> -p 5432 -U <admin-user> -d postgres \
--     -v app_db=initdb -f docker/initdb.sql
--
-- 脚本执行完成后，启动业务镜像。应用启动程序会自动执行 Django
-- migrations，创建全部业务表并升级到当前代码对应的最新结构。

\set ON_ERROR_STOP on

\if :{?app_db}
\else
\set app_db 'initdb'
\endif

\echo 'Preparing PostgreSQL database:' :app_db

SELECT format(
    'CREATE DATABASE %I WITH TEMPLATE template0 ENCODING ''UTF8''',
    :'app_db'
)
WHERE NOT EXISTS (
    SELECT 1
    FROM pg_catalog.pg_database
    WHERE datname = :'app_db'
) \gexec

\connect :"app_db"

CREATE EXTENSION IF NOT EXISTS vector;

SELECT
    current_database() AS database_name,
    current_user AS database_owner,
    extversion AS vector_version
FROM pg_catalog.pg_extension
WHERE extname = 'vector';

\echo 'Database bootstrap completed. Start the application to run Django migrations.'

# Atlas — 内部文档系统

供 4–5 人小团队使用的内部文档管理系统，承载 AI 生成的 HTML 文档页面，支持在线编辑、版本管理与按需发布。

## 快速开始

### 前置要求

安装 [uv](https://docs.astral.sh/uv/getting-started/installation/)：

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 本地开发

```bash
# 同步所有依赖（自动创建 .venv）
uv sync --all-extras

# 复制环境变量模板
cp .env.example .env

# 建库
uv run manage.py migrate

# 创建管理员账号
uv run manage.py createsuperuser

# 启动开发服务器
uv run manage.py runserver
```

打开 http://127.0.0.1:8000

### 代码质量

提交前必跑：

```bash
uv run ruff format .
uv run ruff check . --fix
uv run ty check
uv run pytest
```

### 依赖管理

```bash
# 添加运行时依赖
uv add <pkg>

# 添加开发依赖
uv add --dev <pkg>

# 禁止使用 pip install
```

## 目录结构

```
docsite/          Django 工程配置
apps/
  documents/      文档、版本、目录树
  editor/         编辑接口、HTML 清洗
  publishing/     发布/撤回、slug 路由
  accounts/       账号、登录、审计日志
  core/           设计 token、公共组件
templates/        全局模板
static/           CSS / JS / 字体
ai_templates/     提供给 AI 的 HTML 模板
data/             SQLite（不入库）
backups/          每日备份（不入库）
```

# 内部文档系统 · 技术文档

> 配套《需求文档》使用。本文档约束实现细节，所有代码生成与人工修改均须遵守。

---

## 一、技术栈总览

| 层 | 技术 | 版本 / 说明 |
|---|---|---|
| 语言 | Python | 3.12+ |
| 包管理 | **uv** | 唯一允许的包管理器 |
| Web 框架 | Django | 6.x |
| 数据库 | SQLite | 开启 WAL 模式 |
| 全文搜索 | SQLite FTS5 | 原生扩展，无需额外依赖 |
| 模板 | Django Templates | 服务端渲染 |
| 前端交互 | HTMX + Alpine.js | 局部刷新 + 微状态管理 |
| 富文本编辑 | 原生 `contentEditable` | 自写工具栏（~200 行 JS） |
| 树形目录 | django-treebeard | 嵌套 + 排序 |
| HTML 清洗 | bleach | 白名单标签/属性 |
| 文本差异 | diff-match-patch | 版本对比 |
| 鉴权 | Django auth + django-axes | 自带 + 防暴破 |
| 静态资源 | WhiteNoise | 单进程托管，无需 nginx |
| 异步任务 | Django 6 内置 tasks | 备份、清理、邮件 |
| 进程管理 | Gunicorn | 2–4 worker |
| 反向代理 | Caddy | 自动 HTTPS |
| 容器化 | Docker + Docker Compose | 一份 compose 启动 |
| 代码质量 | **ruff**（lint + format）、**ty**（类型检查） | 全部内嵌 pre-commit |

**版本锁定**：所有依赖严格通过 `pyproject.toml` 与 `uv.lock` 管理，不允许 `pip install` 全局安装。

---

## 二、项目结构

```
docsite/
├── pyproject.toml              # uv 项目定义
├── uv.lock                     # 锁文件，必须提交
├── .python-version             # 3.12
├── manage.py
├── .env.example                # 配置样板
├── .gitignore
├── Caddyfile
├── docker-compose.yml
├── Dockerfile
├── README.md
├── docsite/                    # Django 工程
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── documents/              # 文档、版本、目录树
│   ├── editor/                 # 编辑接口、清洗、校验
│   ├── publishing/             # 发布/撤回、slug 路由
│   ├── accounts/               # 账号、登录、审计日志
│   └── core/                   # 设计 token、模板组件
├── templates/                  # 全局模板
│   ├── base.html               # 含 design tokens CSS 变量
│   ├── doc/                    # 公开阅读页
│   └── admin_ui/               # 管理后台
├── static/
│   ├── css/                    # 主样式（按 token 编写）
│   ├── js/                     # 编辑器、HTMX 扩展
│   └── fonts/                  # 自托管字体
├── ai_templates/               # 提供给 Codex/Claude 的 HTML 模板
│   ├── README.md
│   ├── article.html
│   ├── compare.html
│   └── steps.html
├── data/                       # SQLite 文件 + 上传媒体（gitignore）
├── backups/                    # 自动备份输出（gitignore）
└── tests/
```

---

## 三、uv 使用规范

### 3.1 强制规则

1. **从不使用 `pip` 或 `pip3` 直接装包**。一律 `uv add`。
2. **从不全局安装 Python**。用 `uv python install 3.12` 让 uv 管理。
3. **不手动建 venv**。`uv sync` 自动创建 `.venv`。
4. **运行 Python 命令一律前缀 `uv run`**。例：`uv run manage.py runserver`。
5. **`uv.lock` 必须提交**，保证团队和服务器环境一致。
6. **生产构建用 `uv sync --frozen --no-dev`**。

### 3.2 常用命令

```bash
# 项目初始化
uv init --python 3.12

# 加运行时依赖
uv add django htmx bleach

# 加开发依赖
uv add --dev ruff ty pytest

# 安装/同步所有依赖到 .venv
uv sync

# 运行 Django 命令
uv run manage.py migrate
uv run manage.py runserver

# 跑测试
uv run pytest

# 升级单个依赖
uv add django@latest

# 检查过时依赖
uv pip list --outdated
```

### 3.3 禁止行为

- ❌ `pip install xxx`
- ❌ `python -m venv .venv` 手动建环境
- ❌ 修改系统 Python（`/usr/bin/python3`）
- ❌ 把 `.venv/` 提交进 git
- ❌ 删 `uv.lock` 重生（破坏可复现性）

---

## 四、数据模型

### 4.1 核心表

```python
# apps/documents/models.py 概要

class Document(models.Model):
    """一篇文档的元信息。"""
    id          = UUIDField(primary_key=True, default=uuid4)
    title       = CharField(max_length=200)
    slug        = SlugField(unique=True, allow_unicode=True)
    status      = CharField(choices=[('draft','draft'),
                                     ('published','published'),
                                     ('archived','archived')],
                            default='draft')
    parent      = TreeForeignKey('self', null=True, blank=True,
                                 related_name='children')
    position    = IntegerField(default=0)  # 同级排序
    owner       = ForeignKey(User, on_delete=PROTECT)
    created_at  = DateTimeField(auto_now_add=True)
    updated_at  = DateTimeField(auto_now=True)
    published_at = DateTimeField(null=True, blank=True)

class DocumentVersion(models.Model):
    """每次保存形成一条版本。"""
    document    = ForeignKey(Document, related_name='versions')
    html        = TextField()            # 清洗后完整 HTML
    editable_blocks = JSONField()        # data-editable 区域提取结果
    author      = ForeignKey(User, on_delete=PROTECT)
    is_auto     = BooleanField(default=False)  # 自动 vs 命名
    note        = CharField(max_length=200, blank=True)
    created_at  = DateTimeField(auto_now_add=True)

class SlugAlias(models.Model):
    """slug 改名时的 301 映射。"""
    old_slug    = SlugField(unique=True, allow_unicode=True)
    document    = ForeignKey(Document)
    created_at  = DateTimeField(auto_now_add=True)

class AuditLog(models.Model):
    """谁、何时、对什么做了什么。"""
    actor       = ForeignKey(User, on_delete=PROTECT)
    action      = CharField(max_length=40)  # create/update/publish/delete
    target_type = CharField(max_length=40)
    target_id   = CharField(max_length=64)
    payload     = JSONField(default=dict)
    created_at  = DateTimeField(auto_now_add=True)
```

### 4.2 全文索引

用 SQLite FTS5 建一张虚拟表，挂触发器同步：

```sql
CREATE VIRTUAL TABLE documents_fts USING fts5(
    title, plain_text,
    content='documents_document', content_rowid='id'
);
```

`plain_text` 由保存时从 HTML 去标签生成，避免搜索结果里出现标签字符。

---

## 五、编码约束

### 5.1 风格

- **格式化**：`ruff format`，行宽 100。
- **lint**：`ruff check`，启用 `E, F, I, B, UP, SIM` 规则集。
- **类型检查**：所有新写的函数加 type hints，CI 跑 `ty check`。
- **import 顺序**：标准库 / 第三方 / 本地，ruff 自动排。
- **中文注释允许**，但变量、函数、类名一律英文。

### 5.2 Django 习惯

- 视图优先用**类视图**（`ListView`, `DetailView`, `UpdateView`），保持一致。
- 表单一律用 **Django Form / ModelForm**，禁止裸 `request.POST` 取值。
- 模板里**不写业务逻辑**，复杂渲染走 template tag。
- ORM 查询**必须用 `.select_related` / `.prefetch_related`** 避免 N+1。
- 任何用户输入到 HTML 的地方默认转义；需要原样输出时**显式标 `mark_safe`**，并先过 bleach。

### 5.3 前端

- CSS 用 design token，全局放在 `:root { --color-bg: #F5F3EE; ... }`。
- 禁止内联 `style`（无论模板还是 JS）。
- JS 写原生 + Alpine 即可，**不引入 React/Vue 等框架**。
- HTMX 请求带 `hx-headers='{"X-CSRFToken": "..."}'`，统一注入。

### 5.4 提交前

```bash
uv run ruff format .
uv run ruff check . --fix
uv run ty check
uv run pytest
```

可装 `pre-commit` 自动跑。

---

## 六、本地环境保护

**所有 AI 与人工操作必须遵守以下铁律**：

### 6.1 禁止的危险操作

- ❌ `rm -rf` 任何**不在当前项目目录下**的路径。
- ❌ `sudo` 任何命令（开发不需要 sudo）。
- ❌ 修改 `~/.bashrc` / `~/.zshrc` / `~/.profile` 等用户级配置。
- ❌ 修改系统包（`apt`、`brew install` 全局工具）——开发环境隔离在 uv 与 Docker 内。
- ❌ 全局 `pip install`（前文已强调）。
- ❌ 直接编辑 `/etc/` 下任何文件。
- ❌ 提交前**不能** `git push --force` 到主分支。
- ❌ 不能在未确认的情况下删除 `data/`、`backups/`、`.env` 文件。

### 6.2 必须的防护

- 所有写操作前先 `git status` 确认工作区干净。
- 数据库迁移前自动备份 SQLite 文件到 `backups/pre-migration-<timestamp>.db`。
- `.env` 永远不入库（`.gitignore` 必含）。
- 密钥（`SECRET_KEY`、第三方 token）一律走环境变量，禁止硬编码。
- 删除文档走**软删除**（`is_deleted` flag），物理删除需手动确认 + 命令行。
- 备份脚本输出到**项目外**或独立挂载卷，防止误删项目时备份一起没。

### 6.3 给 Claude Code / Codex 的约束（写进 `CLAUDE.md`）

```markdown
- 永远使用 uv，不使用 pip。
- 永远在 .venv 内运行 Python，不动系统 Python。
- 任何破坏性命令（rm、drop table、migrate --fake-initial）执行前必须先停下来描述意图并等待确认。
- 修改数据库 schema 前自动生成迁移 + 备份。
- 不许 git push --force。
- 不许碰 ~/.bashrc 等用户级配置。
- 不许装系统级包。
```

---

## 七、安全要点

### 7.1 鉴权

- 用 Django 自带 `User` 模型 + `django-axes` 防暴破（5 次失败锁 15 分钟）。
- 密码哈希默认 Argon2，需在 `settings.py` 显式启用：
  ```python
  PASSWORD_HASHERS = [
      "django.contrib.auth.hashers.Argon2PasswordHasher",
      "django.contrib.auth.hashers.PBKDF2PasswordHasher",
  ]
  ```
- session cookie 加 `Secure`、`HttpOnly`、`SameSite=Lax`。
- CSRF 全开，HTMX 请求统一注入 token。

### 7.2 HTML 清洗

bleach 白名单严格定义（写在 `apps/editor/sanitizer.py`）：

```python
ALLOWED_TAGS = {
    'p', 'h1', 'h2', 'h3', 'h4',
    'strong', 'em', 'a', 'br',
    'ul', 'ol', 'li',
    'blockquote', 'code', 'pre',
    'div', 'span', 'section', 'article',
    'img',  # 仅允许 src 在白名单 host
}
ALLOWED_ATTRS = {
    '*': ['class', 'id', 'data-editable', 'data-editable-id'],
    'a': ['href', 'title', 'rel'],
    'img': ['src', 'alt', 'width', 'height'],
}
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']
```

**禁止**：`<script>`、`<iframe>`、`on*` 事件、`javascript:` 协议、`style` 属性。

### 7.3 中间件鉴权 + 视图二次校验

由于 CVE-2025-29927 类问题历史教训，**绝不只靠中间件**做权限：

- 中间件做粗筛（未登录 → 跳 `/login`）。
- 每个写操作的视图函数**再次**用 `@login_required` + `PermissionRequiredMixin` 校验。
- 发布 / 删除 / 用户管理类操作要求**重新输入密码**。

### 7.4 文件上传

- 仅管理员可上传图片。
- 限制 MIME 类型（白名单：jpg / png / webp / svg）。
- SVG 必须再过一次清洗（防 SVG XSS）。
- 文件名重命名为 UUID，禁止用户原文件名落盘。
- 文件存到 `data/media/<year>/<month>/`，权限 `0644`。

### 7.5 备份

- `django.tasks` 每天 03:00 跑备份任务：
  - `sqlite3 .backup` 命令安全复制 db 文件。
  - 复制到 `backups/<date>.db`。
  - 保留 30 天，超出 删除。
- 备份输出**只能写到指定目录**，路径硬编码，绝不接受用户输入。

---

## 八、部署方案

### 8.1 单机部署（推荐起步）

一台 2C4G 的小机器即可，比如 4–5 美元/月的 VPS。

**Docker Compose** 起两个服务：

```yaml
services:
  app:
    build: .
    volumes:
      - ./data:/app/data
      - ./backups:/app/backups
    environment:
      - DJANGO_SETTINGS_MODULE=docsite.settings.prod
    restart: unless-stopped

  caddy:
    image: caddy:2-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
    restart: unless-stopped
```

**Caddyfile** 极简：

```
docs.example.com {
    reverse_proxy app:8000
    encode gzip zstd
}
```

Caddy 自动签发 Let's Encrypt 证书，无需任何配置。

### 8.2 进程

容器内用 Gunicorn：

```bash
uv run gunicorn docsite.wsgi:application \
    --workers 3 --bind 0.0.0.0:8000 \
    --access-logfile - --error-logfile -
```

### 8.3 持久化

- `./data/` 挂卷：SQLite 文件 + 上传媒体。
- `./backups/` 挂卷：每日备份。
- 强烈建议**再加一个云端异地备份**（rclone 同步到对象存储），脚本独立于应用。

---

## 九、Skills 使用建议

按任务类型推荐你的可用 skills：

### 9.1 项目初始化

- **`init`** — 初始化 `CLAUDE.md`，把第六节"本地环境保护"和"uv 规范"写进去。
- **`modern-python`** — 配置 uv + ruff + ty + pyproject.toml，建议第一步就跑。

### 9.2 写代码阶段

- **`simplify`** — Claude 写完一段代码后跑一遍，去重、简化、移除冗余。
- **`sharp-edges`** — 检查危险 API、不安全默认值（重要：Django settings 用前必跑）。
- **`insecure-defaults`** — 配 settings 时跑一遍，避免 DEBUG=True 上线之类的低级错误。

### 9.3 前端 / UI

- **`impeccable`** — 设计完登录页、编辑器、阅读页等关键界面后跑，按设计 token 审查。
- **`frontend-design-review`** — 完整页面成型后做生产级评审。
- **`web-design-guidelines`** — 检查可访问性、对比度、焦点态。

### 9.4 安全与质量

- **`security-review`** — 鉴权、bleach 清洗、文件上传相关 PR 必跑。
- **`differential-review`** — 改动复杂时按 diff 评审，比整文件审查更精准。
- **`review`** — 通用 PR 审查。
- **`audit-context-building`** — 超细粒度审查，复杂逻辑（如版本 diff、目录树拖拽）跑这个。

### 9.5 协作

- **`github`** — PR 管理、分支策略。
- **`schedule`** / **`loop`** — 定时跑 lint、备份验证、依赖更新检查。

### 9.6 建议补充的 skills

按需可通过 `find-skills` 或 `skill-creator` 找/造：

- **`django-best-practices`**（如不存在可自造）— Django 特有的反模式检查。
- **`htmx-patterns`** — HTMX 写法约定。
- **`accessibility-audit`** — WCAG 合规检查。
- **`sqlite-migration-safety`** — 迁移前自动备份、迁移失败回滚。
- **`bleach-config-review`** — HTML 清洗白名单审查（关键安全点）。

### 9.7 不要无脑跑

skills 是工具不是仪式。**简单改动跑了反而拖累节奏**。约定：

- 写关键安全代码 → 跑 `security-review` + `insecure-defaults`。
- 写 UI → 跑 `impeccable`。
- 大重构 → 跑 `audit-context-building` + `simplify`。
- 日常 typo 修复 → 不跑任何 skill。

---

## 十、潜在问题与预案

| 问题 | 触发条件 | 预案 |
|---|---|---|
| SQLite 并发写锁 | 多人同时编辑同一文档 | 开启 WAL，前端用乐观锁（version_id 校验），冲突时提示"已被他人修改"。 |
| 编辑器丢失改动 | 用户误关页面 | 自动保存 + `beforeunload` 提示 + localStorage 暂存草稿（仅本机）。 |
| AI 生成 HTML 不合规 | Codex/Claude 偏离模板 | 导入前 schema 校验，给出明确错误位置和修正建议。 |
| 备份文件占满磁盘 | 长期运行 | 每日清理 30 天前的备份，磁盘监控告警。 |
| Caddy 证书续签失败 | DNS 故障 / 域名过期 | Caddy 自带 30 天重试窗口；监控脚本检查证书有效期。 |
| Django 安全更新 | CVE 披露 | 订阅 djangoproject 安全列表；CI 跑 `pip-audit`（uv 内置等价）。 |
| 团队成员离职 | 账号继续可登录 | 管理后台一键禁用 + 强制 session 失效。 |
| HTML 富文本破坏布局 | 编辑时误删 `data-editable` 外层结构 | contentEditable 锁定在指定区域，外层元素 `contenteditable="false"` 且 JS 拦截 DOM 修改。 |

---

## 十一、上线前自检清单

部署前**逐条勾选**：

- [ ] `DEBUG = False`
- [ ] `SECRET_KEY` 从环境变量读，不在仓库
- [ ] `ALLOWED_HOSTS` 配置正确
- [ ] HTTPS 强制（`SECURE_SSL_REDIRECT = True`）
- [ ] Session / CSRF cookie 加 Secure
- [ ] django-axes 已启用
- [ ] bleach 白名单已审查
- [ ] 每日备份脚本已部署且测试过恢复流程
- [ ] 管理员密码强度足够（建议 16 位以上）
- [ ] Caddy 证书签发成功
- [ ] 错误页（404、500）已自定义为系统设计风格
- [ ] 日志轮转配置（avoid 日志填满磁盘）
- [ ] 至少做过一次**完整流程演练**：导入 → 编辑 → 发布 → 撤回 → 还原历史版本

---

*文档结束。版本约定：每次架构性变更需更新本文档并标注日期。*

# CLAUDE.md — 项目协作约定

> 本文件是执行者每次开工的必读文件。所有代码生成、修改、执行命令前先读这里。

---

## 项目背景

一个内部 HTML 文档管理系统，承载外部 AI 或人工生成的完整 HTML 文档页面。
小团队（4–5 人）使用，单机部署。

完整规格见：
- `docs/执行计划-V2.0.md` — 当前整改方案与执行边界
- `PRODUCT.md` — 产品定位
- `DESIGN.md` — UI 设计系统（颜色、字体、组件、动效）的唯一权威，位于项目根目录
- `skills/html-document/SKILL.md` — HTML 文档生成 skill，作为 seed 内容读取，不主动改写

注意：当前 V2 整改中，如文档冲突，以 `docs/执行计划-V2.0.md` 为准；视觉细节以根目录 `DESIGN.md` 为准。若两者都没明确，停下来问。

**写任何代码前先确认对应章节，不要凭印象。**

---

## 铁律（违反任意一条都属于严重错误）

### 环境与命令

1. **包管理只用 `uv`**。`pip`、`pip3`、`pipenv`、`poetry` 一律禁止。
2. **运行 Python 一律前缀 `uv run`**。不要直接 `python xxx.py`。
3. **不动系统 Python**（`/usr/bin/python3`）。需要 Python 版本切换用 `uv python install`。
4. **不用 `sudo`**。开发不需要。
5. **不装系统级包**（`apt install`、`brew install` 全局工具）。需要的工具进 `uv add --dev`。
6. **不改用户配置**（`~/.bashrc`、`~/.zshrc`、`~/.profile`）。

### 文件与 Git

7. **`rm -rf` 只能用在当前项目目录内，且必须事先口头说明意图等待确认**。
8. **不许 `git push --force` 到主分支**。要 force push 先说明。
9. **不许提交 `.env`、`.venv/`、`data/`、`backups/`、`*.db`**。检查 `.gitignore`。
10. **`uv.lock` 必须提交**，不许随意 `rm uv.lock` 重生。

### 数据库

11. **跑 migration 前自动备份**：`cp data/db.sqlite3 backups/pre-migration-$(date +%Y%m%d-%H%M%S).db`。
12. **不许 `migrate --fake-initial`**，除非明确说明并等待确认。
13. **删数据用软删除**（`is_deleted=True`），不直接 `DELETE FROM`。

### 安全

14. **密钥永远走环境变量**，禁止硬编码。检查任何 `SECRET_KEY`、`API_KEY`、密码字符串。
15. **人类填写的系统字段**（标题、备注、用户名等）必须清洗或转义后再渲染；**文档主体 HTML** 走 iframe sandbox + CSP 隔离，不经 bleach 重写。
16. **新写视图必须有 `@login_required` 或显式公开声明**。两者必居其一。

---

## 命令速查

```bash
# 安装/同步依赖
uv sync

# 加依赖
uv add <pkg>              # 运行时
uv add --dev <pkg>        # 开发时

# 跑 Django
uv run manage.py runserver
uv run manage.py makemigrations
uv run manage.py migrate
uv run manage.py createsuperuser

# 代码质量（提交前必跑）
uv run ruff format .
uv run ruff check . --fix
uv run ty check
uv run pytest

# 备份
cp data/db.sqlite3 backups/manual-$(date +%Y%m%d-%H%M%S).db
```

---

## 代码风格

- **格式化**：ruff format，行宽 100。
- **lint**：ruff check，规则集 `E, F, I, B, UP, SIM`。
- **类型**：所有新函数加 type hints。
- **命名**：变量/函数/类一律英文，注释可中文。
- **视图**：优先类视图（`ListView` 等），保持一致。
- **ORM**：必须 `.select_related` / `.prefetch_related`，避免 N+1。
- **模板**：不写业务逻辑，复杂渲染走 template tag。
- **前端 JS**：原生 + Alpine.js，禁止引入 React/Vue。
- **CSS**：用 `:root` 里的 design token 变量，不写硬编码颜色。
- **HTML 模板**：禁止内联 `style`。

---

## 任务交付前必做（每个阶段）

1. `uv run ruff format . && uv run ruff check . --fix`
2. `uv run ty check`
3. `uv run pytest`（如果有相关测试）
4. 手动跑一遍主流程验证
5. `git add -A && git commit -m "feat(<scope>): <desc>"`
6. 简短报告：完成了什么、跳过了什么、遗留什么、下一步建议

---

## 沟通约定

- **回答用中文**。
- **简练，不堆套话**。不需要"我会努力为您..."这类。
- **不确定就停下问**，不要猜测乱写。
- **做了破坏性操作（删文件、改 schema、改配置）必须先说明**。
- **失败了直接说失败**，不要硬撑或编。
- 凡涉及前端、模板、CSS、用户可见界面元素的任务，必须翻阅 DESIGN.md 找出
  对应组件规范后再开始写代码。仅后端、devops、数据层任务可跳过。
- 如不确定某元素是否有 DESIGN.md 规范，先问，不要凭印象写。

---

## 当我说"按文档实现 X"时

- 优先找到 `docs/执行计划-V2.0.md` 里的对应章节并引用章节号；涉及视觉时同时查根目录 `DESIGN.md`。
- 先列实现计划（不超过 8 步），等确认再写代码。
- 实现过程中如发现文档遗漏或矛盾，停下来问，不要自行决断。

---
version: alpha
name: ai-docsite-claude-inspired
description: 一个面向 AI 生成文档托管与小团队编辑后台的暖白文档系统。视觉基底跟随 Claude Code Docs 的 tinted cream canvas, 以 #faf9f5 作为页面底色, 以 Anthropic 式 muted coral #cc785c 作为唯一主行动色。系统不靠大量线条、边框或卡片制造结构, 而是用 96px section rhythm、清晰的排版层级、浅奶油色 surface 切换、少量暗色代码面板来组织内容。交互参考 Apple 的轻量粘性导航、平滑锚点跳转、按压缩放和内容优先的滚动节奏。

colors:
  # Brand & Action
  primary: "#cc785c"
  primary-hover: "#b86950"
  primary-pressed: "#a9583e"
  primary-disabled: "#e6dfd8"
  on-primary: "#ffffff"

  # Surface
  canvas: "#faf9f5"
  surface-soft: "#f5f0e8"
  surface-card: "#efe9de"
  surface-strong: "#e8e0d2"
  surface-raised: "#fffdf8"
  surface-overlay: "rgba(20, 20, 19, 0.38)"
  surface-dark: "#181715"
  surface-dark-soft: "#1f1e1b"
  surface-dark-elevated: "#252320"

  # Hairline
  hairline: "#e6dfd8"
  hairline-soft: "#ebe6df"
  hairline-strong: "#d8cec2"

  # Ink
  ink: "#141413"
  ink-strong: "#252523"
  ink-body: "#3d3d3a"
  ink-muted: "#6c6a64"
  ink-subtle: "#8e8b82"
  ink-on-dark: "#faf9f5"
  ink-on-dark-muted: "#a09d96"

  # Semantic
  success: "#4f9b65"
  success-surface: "#edf5ee"
  warning: "#b9832f"
  warning-surface: "#fbf1df"
  danger: "#c64545"
  danger-surface: "#fbebea"

  # Interaction
  focus-ring: "rgba(204, 120, 92, 0.28)"
  link-hover-fill: "rgba(204, 120, 92, 0.08)"
  selection: "rgba(204, 120, 92, 0.18)"

  # Diff
  diff-add-surface: "#e8f3eb"
  diff-add-ink: "#27623b"
  diff-del-surface: "#f8e4e1"
  diff-del-ink: "#9f312d"

typography:
  display-xl:
    fontFamily: "'Tiempos Headline', 'Cormorant Garamond', 'Noto Serif SC', Georgia, serif"
    fontSize: 56px
    fontWeight: 400
    lineHeight: 1.08
    letterSpacing: 0
  display-lg:
    fontFamily: "'Tiempos Headline', 'Cormorant Garamond', 'Noto Serif SC', Georgia, serif"
    fontSize: 44px
    fontWeight: 400
    lineHeight: 1.12
    letterSpacing: 0
  display-md:
    fontFamily: "'Tiempos Headline', 'Cormorant Garamond', 'Noto Serif SC', Georgia, serif"
    fontSize: 32px
    fontWeight: 400
    lineHeight: 1.2
    letterSpacing: 0
  display-sm:
    fontFamily: "'Tiempos Headline', 'Cormorant Garamond', 'Noto Serif SC', Georgia, serif"
    fontSize: 24px
    fontWeight: 400
    lineHeight: 1.28
    letterSpacing: 0
  title-lg:
    fontFamily: "'Inter', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: 22px
    fontWeight: 500
    lineHeight: 1.35
    letterSpacing: 0
  title-md:
    fontFamily: "'Inter', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: 18px
    fontWeight: 500
    lineHeight: 1.45
    letterSpacing: 0
  body:
    fontFamily: "'Inter', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.68
    letterSpacing: 0
  body-reading:
    fontFamily: "'Inter', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: 17px
    fontWeight: 400
    lineHeight: 1.76
    letterSpacing: 0
  body-sm:
    fontFamily: "'Inter', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: 0
  meta:
    fontFamily: "'Inter', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.45
    letterSpacing: 0
  label:
    fontFamily: "'Inter', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: 12px
    fontWeight: 500
    lineHeight: 1.35
    letterSpacing: 0
  button:
    fontFamily: "'Inter', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    fontSize: 14px
    fontWeight: 500
    lineHeight: 1.2
    letterSpacing: 0
  mono:
    fontFamily: "'JetBrains Mono', 'SF Mono', Consolas, ui-monospace, monospace"
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.65
    letterSpacing: 0

rounded:
  xs: 4px
  sm: 6px
  md: 8px
  lg: 8px
  xl: 12px
  pill: 9999px
  full: 9999px

spacing:
  xxs: 4px
  xs: 8px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 32px
  xxl: 48px
  section-tight: 72px
  section: 96px

shadow:
  none: "none"
  focus: "0 0 0 3px {colors.focus-ring}"
  floating: "0 16px 48px rgba(20, 20, 19, 0.10)"
  popover: "0 12px 32px rgba(20, 20, 19, 0.12)"

motion:
  duration-fast: 120ms
  duration-base: 180ms
  duration-slow: 320ms
  duration-route: 420ms
  ease-standard: "cubic-bezier(0.4, 0, 0.2, 1)"
  ease-out: "cubic-bezier(0.22, 1, 0.36, 1)"
  press-scale: 0.97

layout:
  public-reader-width: 760px
  docs-shell-width: 1280px
  admin-shell-width: 1360px
  sidebar-width: 264px
  toc-width: 220px
  top-nav-height: 64px
  content-padding-desktop: 48px
  content-padding-tablet: 32px
  content-padding-mobile: 20px

components:
  # Buttons
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: "10px 18px"
    height: 40px
    border: "1px solid transparent"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-primary-pressed:
    backgroundColor: "{colors.primary-pressed}"
    transform: "scale({motion.press-scale})"
  button-primary-disabled:
    backgroundColor: "{colors.primary-disabled}"
    textColor: "{colors.ink-subtle}"

  button-secondary:
    backgroundColor: "{colors.surface-soft}"
    textColor: "{colors.ink}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: "10px 18px"
    height: 40px
    border: "1px solid transparent"
  button-secondary-hover:
    backgroundColor: "{colors.surface-card}"
  button-secondary-pressed:
    transform: "scale({motion.press-scale})"

  button-ghost:
    backgroundColor: transparent
    textColor: "{colors.ink}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: "10px 12px"
    height: 40px
  button-ghost-hover:
    backgroundColor: "{colors.link-hover-fill}"
    textColor: "{colors.primary}"

  button-danger:
    backgroundColor: "{colors.danger-surface}"
    textColor: "{colors.danger}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: "10px 18px"
    height: 40px
    border: "1px solid transparent"

  icon-button:
    backgroundColor: transparent
    textColor: "{colors.ink-muted}"
    rounded: "{rounded.full}"
    size: 40px
  icon-button-hover:
    backgroundColor: "{colors.surface-soft}"
    textColor: "{colors.ink}"

  # Form
  text-input:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "10px 14px"
    height: 40px
    border: "1px solid {colors.hairline}"
  text-input-hover:
    border: "1px solid {colors.hairline-strong}"
  text-input-focused:
    border: "1px solid {colors.primary}"
    shadow: "{shadow.focus}"
  text-input-error:
    border: "1px solid {colors.danger}"
    backgroundColor: "{colors.danger-surface}"
  search-command:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink-muted}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.md}"
    padding: "8px 12px"
    height: 40px
    border: "1px solid {colors.hairline}"

  # Reading content
  article-shell:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink-body}"
    typography: "{typography.body-reading}"
    maxWidth: "{layout.public-reader-width}"
  article-title:
    textColor: "{colors.ink}"
    typography: "{typography.display-lg}"
  article-section-title:
    textColor: "{colors.ink}"
    typography: "{typography.display-md}"
  article-meta:
    textColor: "{colors.ink-muted}"
    typography: "{typography.meta}"
  info-callout:
    backgroundColor: "{colors.surface-soft}"
    textColor: "{colors.ink-body}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "20px 24px"
    border: "1px solid transparent"
  content-card:
    backgroundColor: "{colors.surface-soft}"
    textColor: "{colors.ink-body}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "24px"
    border: "1px solid transparent"
  code-block:
    backgroundColor: "{colors.surface-dark}"
    textColor: "{colors.ink-on-dark}"
    typography: "{typography.mono}"
    rounded: "{rounded.md}"
    padding: "20px 24px"
  table:
    backgroundColor: transparent
    textColor: "{colors.ink-body}"
    typography: "{typography.body-sm}"
    rowBorder: "1px solid {colors.hairline-soft}"

  # Claude-like docs shell
  top-nav:
    backgroundColor: "rgba(250, 249, 245, 0.86)"
    backdropFilter: "blur(18px)"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    height: "{layout.top-nav-height}"
    borderBottom: "1px solid rgba(230, 223, 216, 0.72)"
  docs-sidebar:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink-muted}"
    typography: "{typography.body-sm}"
    width: "{layout.sidebar-width}"
    borderRight: "1px solid rgba(230, 223, 216, 0.60)"
  docs-sidebar-item-active:
    backgroundColor: "{colors.surface-soft}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
  docs-toc:
    backgroundColor: transparent
    textColor: "{colors.ink-muted}"
    typography: "{typography.body-sm}"
    width: "{layout.toc-width}"
  docs-toc-item-active:
    textColor: "{colors.primary}"

  # Admin
  admin-shell:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
  admin-sidebar:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink-muted}"
    typography: "{typography.body-sm}"
    width: "{layout.sidebar-width}"
    borderRight: "1px solid rgba(230, 223, 216, 0.60)"
  admin-panel:
    backgroundColor: "{colors.surface-soft}"
    textColor: "{colors.ink-body}"
    rounded: "{rounded.md}"
    padding: "24px"
    border: "1px solid transparent"
  editor-toolbar:
    backgroundColor: "rgba(250, 249, 245, 0.92)"
    backdropFilter: "blur(18px)"
    textColor: "{colors.ink}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: "6px"
    shadow: "{shadow.popover}"
  editable-region:
    backgroundColor: transparent
    outline: "1px dashed rgba(204, 120, 92, 0.46)"
    rounded: "{rounded.sm}"
  editable-region-hover:
    backgroundColor: "rgba(204, 120, 92, 0.05)"

  # Feedback
  toast:
    backgroundColor: "{colors.surface-dark}"
    textColor: "{colors.ink-on-dark}"
    typography: "{typography.body-sm}"
    rounded: "{rounded.md}"
    padding: "12px 16px"
    shadow: "{shadow.popover}"
  drawer:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    width: 460px
    shadow: "{shadow.floating}"
  search-overlay:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.xl}"
    width: 640px
    shadow: "{shadow.floating}"

  # Status
  badge:
    backgroundColor: "{colors.surface-soft}"
    textColor: "{colors.ink-muted}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "4px 10px"
  badge-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "4px 10px"
  status-dot-published:
    backgroundColor: "{colors.success}"
    size: "8px"
    rounded: "{rounded.full}"
  status-dot-draft:
    backgroundColor: "{colors.ink-subtle}"
    size: "8px"
    rounded: "{rounded.full}"
  status-dot-archived:
    backgroundColor: "{colors.danger}"
    size: "8px"
    rounded: "{rounded.full}"

  # Diff
  diff-add:
    backgroundColor: "{colors.diff-add-surface}"
    textColor: "{colors.diff-add-ink}"
  diff-del:
    backgroundColor: "{colors.diff-del-surface}"
    textColor: "{colors.diff-del-ink}"
    textDecoration: "line-through"
---

## Overview

这套设计系统服务两类使用者:

- **公开访客** 通过 `/d/<slug>` 直接打开一篇文档。页面应该像 Claude Code Docs 的正文区一样安静, 暖白底、清晰标题、宽松上下间距, 不出现登录入口、编辑入口、营销导航或多余品牌露出。
- **团队编辑** 进入 `/admin/` 管理 AI 生成文档。后台可以采用 Claude Code Docs 式三栏文档 shell: 左侧目录, 中央编辑或预览, 右侧页内目录或版本信息。它是工作台, 但仍然保持克制。

新的方向从旧版的深绿 + 金色出版物语言切换为 **Claude 式暖白 + 珊瑚色行动语言**。底色固定使用 `{colors.canvas}` `#faf9f5`; 主按钮、焦点、链接只使用 `{colors.primary}` `#cc785c`; 线条只在导航分隔、输入框、表格行、侧栏边界这些功能性位置出现。

Apple 的参考不直接改变视觉品牌, 只吸收交互节奏: 粘性顶部栏、轻量 backdrop blur、锚点平滑滚动、按钮按压缩放、页面切换时内容优先而不是动画优先。

**关键特征**

- **Claude 暖白底**: body、nav、阅读页全部以 `#faf9f5` 为底, 不使用纯白大面积画布。
- **唯一主行动色**: 珊瑚色 `#cc785c` 用于主按钮、文本链接、focus ring、选中文本和少量 badge。
- **少线条、少框**: 删除旧版顶部进度条、金色引用线、大量卡片边框。层次主要来自留白、字号、浅奶油色 surface 和暗色代码块。
- **标题有编辑感**: h1/h2 使用衬线 display, UI 与正文使用 Inter / Noto Sans SC。所有 letter-spacing 保持 0, 不靠负字距制造风格。
- **大间距**: section 默认 96px, 紧凑 section 72px, 卡片或 callout 内边距 24px 到 32px。
- **内容优先**: 公开阅读页以 760px 主内容宽度为上限, 长文读起来像一篇被认真排过的文档, 不是 CMS 模板。
- **代码与产品 chrome 用暗色面板**: 代码块、版本 diff 预览、AI 生成日志可以使用 `{colors.surface-dark}`, 模仿 Claude developer 页面里的产品感。

## Colors

### Brand & Action

- **Primary** (`{colors.primary}` `#cc785c`): 所有主行动按钮、链接、focus ring、选中态的来源。不要再使用深绿或金色作为行动色。
- **Primary Hover / Pressed**: hover 使用 `#b86950`, pressed 使用 `#a9583e`。pressed 同时配合 `transform: scale(0.97)`。
- **Primary Disabled** (`#e6dfd8`): 和 hairline 同色系, 禁用态看起来像沉回背景里。

### Surface

- **Canvas** (`#faf9f5`): 全站底色, 与 Claude 参考保持一致。不要换成纯白或冷灰。
- **Surface Soft** (`#f5f0e8`): 轻分区、hover、callout 背景。
- **Surface Card** (`#efe9de`): 比 soft 更明显的分区, 用于少量功能面板、空状态、tab active。
- **Surface Raised** (`#fffdf8`): 仅用于浮层内部或非常小的输入承载面, 不做大面积页面底色。
- **Surface Dark** (`#181715`): 代码块、命令输出、发布前预览、重要系统 toast。

### Hairline

线条是功能提示, 不是装饰。

- **Hairline** (`#e6dfd8`): 输入框、搜索框、顶栏下边界。
- **Hairline Soft** (`#ebe6df`): 表格行、列表分隔、侧栏内部分组。
- **Hairline Strong** (`#d8cec2`): 输入框 hover 或需要增强可点性的状态。

不要给每个卡片都加边框。Claude 的页面结构感来自内容、目录和留白, 不是一格一格的盒子。

### Ink

- **Ink** (`#141413`): 标题和关键 UI。
- **Ink Body** (`#3d3d3a`): 正文默认色, 比标题更柔和。
- **Ink Muted** (`#6c6a64`): meta、sidebar、helper text。
- **Ink Subtle** (`#8e8b82`): placeholder、禁用文本、低优先级时间戳。
- **Ink On Dark** (`#faf9f5`): 暗色代码块上的文字, 呼应页面底色。

### Semantic

语义色只用于状态, 不变成品牌色。

- **Success**: 保存成功、已发布。
- **Warning**: 待发布、存在未保存变更。
- **Danger**: 删除、校验错误、归档。

每个语义色都有浅 surface, 用于提示条或 inline validation。

## Typography

### Font Family

| 角色 | 字体 | 用途 |
|---|---|---|
| Display | `Tiempos Headline` / `Cormorant Garamond` / `Noto Serif SC` | 文档 h1、section h2、重大空状态 |
| Body / UI | `Inter` / `Noto Sans SC` / system-ui | 正文、按钮、输入框、导航、后台 |
| Mono | `JetBrains Mono` / `SF Mono` | 代码、slug、命令、diff |

中文场景下, display 字体必须能覆盖中文。若没有 Tiempos 授权, 用 `Noto Serif SC` 承担中文标题, 西文 fallback 可用 Cormorant Garamond。

### Hierarchy

| Token | Size | Weight | Line | 用途 |
|---|---:|---:|---:|---|
| `{typography.display-xl}` | 56px | 400 | 1.08 | 大型欢迎页或空状态, 少用 |
| `{typography.display-lg}` | 44px | 400 | 1.12 | 公开文档主标题 |
| `{typography.display-md}` | 32px | 400 | 1.20 | 文档 section 标题 |
| `{typography.display-sm}` | 24px | 400 | 1.28 | callout 标题、小节标题 |
| `{typography.title-lg}` | 22px | 500 | 1.35 | 后台页面标题、面板标题 |
| `{typography.title-md}` | 18px | 500 | 1.45 | 列表项标题、表单组标题 |
| `{typography.body-reading}` | 17px | 400 | 1.76 | 公开阅读页正文 |
| `{typography.body}` | 16px | 400 | 1.68 | 后台正文、表单说明 |
| `{typography.body-sm}` | 14px | 400 | 1.55 | sidebar、footer、helper |
| `{typography.meta}` | 13px | 400 | 1.45 | 日期、作者、版本 |
| `{typography.label}` | 12px | 500 | 1.35 | badge、tab、状态 |
| `{typography.button}` | 14px | 500 | 1.20 | 按钮 |
| `{typography.mono}` | 13px | 400 | 1.65 | 代码和命令 |

### Principles

- **标题用衬线, UI 用无衬线**。这是 Claude 风格中最重要的编辑感来源。
- **正文不再用 300 字重**。Claude 的文档正文更稳定, 默认 400 更适合管理后台和长文。
- **letter-spacing 始终为 0**。不要为了模仿英文页面而在中文环境里使用负字距。
- **长文正文用 17px / 1.76**。公开阅读页优先舒适, 后台界面用 16px / 1.68 保持效率。
- **代码块用暗色面板**。代码与命令是 Claude Code 类页面的主要视觉锚点, 不要做成浅灰小盒子。

## Layout

### Spacing System

基础单位 4px:

- `{spacing.xxs}` 4px
- `{spacing.xs}` 8px
- `{spacing.sm}` 12px
- `{spacing.md}` 16px
- `{spacing.lg}` 24px
- `{spacing.xl}` 32px
- `{spacing.xxl}` 48px
- `{spacing.section-tight}` 72px
- `{spacing.section}` 96px

规则:

- 页面大 section 上下默认 96px。
- 文档内 h2 距离上一段内容 72px, 标题后到正文 20px 到 24px。
- 段落之间 16px 到 20px。
- callout 和内容面板内边距 24px, 大型后台面板 32px。
- 列表项之间优先用 8px 到 12px gap, 不用线条分割。

### Public Reader

公开阅读页是最克制的页面。

| 视口 | 内容宽度 | 左右 padding |
|---|---:|---:|
| Desktop | 760px | 48px |
| Tablet | 100% | 32px |
| Mobile | 100% | 20px |

页面结构:

```text
body canvas #faf9f5
  main article 760px
    meta / collection label
    h1
    lead paragraph
    content sections with 96px rhythm
    footer meta
```

公开阅读页不使用顶部进度条, 不使用品牌 logo, 不显示编辑入口。必要时可以在页面底部放一行 muted meta: 最后更新日期、版本号、公开链接状态。

### Docs / Admin Shell

后台和内部文档浏览可以使用 Claude Code Docs 式三栏:

```text
top nav 64px, warm translucent canvas
content shell max 1280px
  left sidebar 264px
  main content flexible, max 760px to 820px
  right toc 220px
```

- 顶部栏 sticky, 使用 `rgba(250,249,245,0.86)` + `backdrop-filter: blur(18px)`。
- 左侧目录只保留一条极淡右边界, 不给每个分组画框。
- 右侧 TOC 不加背景, active 文字用 primary。
- 页面分区靠标题和留白, 不靠横线。

### Admin Workbench

后台不是营销页, 也不是 Notion 块编辑器。它应该像文档工具:

- 左侧: 文档树、搜索、状态筛选、新建文档。
- 中央: 当前文档编辑或预览。
- 右侧: 版本、发布状态、AI 生成记录或页内目录。
- 面板使用 `{colors.surface-soft}` 无边框色块; 只有输入框、表格行、侧栏边界使用 hairline。

## Elevation & Depth

| 层级 | 处理 | 用途 |
|---|---|---|
| Flat | canvas 背景, 无边框无阴影 | 正文、普通 section |
| Soft surface | `{colors.surface-soft}` 色块, 无边框 | callout、空状态、后台面板 |
| Hairline control | 1px hairline | 输入框、搜索框、表格行、侧栏边界 |
| Dark product surface | `{colors.surface-dark}` | 代码块、命令、AI 日志、重要 toast |
| Floating | backdrop blur + 轻阴影 | 搜索浮层、toolbar、drawer |

不要把每个信息块都做成白卡片。Claude 的页面不是卡片堆叠, 而是内容流。浮层可以有阴影, 页面内普通内容不使用阴影。

## Shapes

| Token | Value | 用途 |
|---|---:|---|
| `{rounded.xs}` | 4px | 小 badge、tiny controls |
| `{rounded.sm}` | 6px | editable outline、列表 active |
| `{rounded.md}` | 8px | 按钮、输入框、callout、代码块、普通面板 |
| `{rounded.lg}` | 8px | 内容面板, 与 md 保持同一视觉语法 |
| `{rounded.xl}` | 12px | 搜索浮层、modal、drawer 内的大容器 |
| `{rounded.pill}` | 9999px | badge、status pill |
| `{rounded.full}` | 9999px | icon button、状态点 |

按钮、输入框和普通面板都以 8px 为主。不要出现大面积 18px 到 24px 的圆角, 这会把文档系统带向消费级卡片感。

## Components

### Buttons

**`button-primary`**  
Claude 式珊瑚色主按钮。40px 高, 8px 圆角, 14px / 500 字体。用于保存、发布、新建、确认。

状态:

- hover: 背景切到 `{colors.primary-hover}`。
- pressed: 背景切到 `{colors.primary-pressed}`, 同时 `transform: scale(0.97)`。
- focus: 3px `{colors.focus-ring}` 外环。
- disabled: `{colors.primary-disabled}` 背景, muted 文本。

**`button-secondary`**  
浅奶油色按钮, 不默认画硬边框。用于取消、返回、次级操作。hover 加深到 `{colors.surface-card}`。

**`button-ghost`**  
透明按钮, hover 出现极淡珊瑚底。用于顶栏、工具栏、行内操作。

**`button-danger`**  
浅红底红字, 不使用红底白字。危险操作需要确认弹层, 按钮本身不大声喊叫。

### Inputs

**`text-input`**  
背景与页面一致用 `{colors.canvas}`, 1px hairline, 8px 圆角, 40px 高。placeholder 用 `{colors.ink-subtle}`。

Focus:

```css
border-color: var(--color-primary);
box-shadow: 0 0 0 3px var(--color-focus-ring);
```

**`search-command`**  
用于全局搜索或 Claude Docs 式 top search。左侧搜索图标, 右侧可以显示 `⌘K` 快捷键胶囊。它是输入框, 不是大卡片。

### Reading Content

**`article-shell`**  
公开文档主容器。max-width 760px, body-reading 字体。无背景、无边框。

**`info-callout`**  
浅奶油色说明块, 无左竖线。用于重要提示、Documentation Index、发布说明。不要用金色线条。

**`content-card`**  
仅用于必须被成组识别的信息, 如版本对比摘要、AI 生成说明。背景 `{colors.surface-soft}`, 无边框, 8px 圆角。

**`code-block`**  
暗色代码块是本系统最强的内容容器。使用 `{colors.surface-dark}`, 代码字体 13px / 1.65, padding 20px 到 24px。复制按钮用 ghost icon button, hover 时出现。

**`table`**  
表格不画完整外框, 只画行分隔。表头使用 `{typography.label}` 和 muted text。

### Docs Navigation

**`top-nav`**  
64px sticky 顶栏, 背景为半透明 canvas + blur。包含产品名、全局搜索、主要入口、登录或发布相关操作。不要塞满链接。

**`docs-sidebar`**  
264px 宽, 背景仍是 canvas。active item 使用 surface-soft 色块和 8px 圆角。分组标题用 label, 分组之间用 24px gap。

**`docs-toc`**  
右侧页内目录, 220px。只显示当前文档 h2/h3。active 用珊瑚色文字, 不加竖线。

### Editor

**`editable-region`**  
编辑模式才出现的 dashed outline, 颜色为 primary 46% alpha。hover 时加 5% 珊瑚底。非编辑模式完全不出现编辑边界。

**`editor-toolbar`**  
浮动工具栏使用半透明 canvas + blur + popover shadow。只包含常用格式和保存操作:

- 加粗
- 斜体
- 链接
- 清除格式
- 撤销
- 重做
- 保存

不提供字体、字号、颜色选择器。风格由系统决定。

### Feedback

**`toast`**  
默认使用暗色 surface, 右下角浮出。保存成功文案示例: `已保存 · 14:32`。错误 toast 可用 danger-surface, 但仍保持 8px 圆角和简短文字。

**`drawer`**  
右侧抽屉, 460px 宽, 用于版本历史、发布确认、AI 生成记录。打开时覆盖半透明 scrim, ESC 关闭。

**`search-overlay`**  
`⌘K` / `Ctrl+K` 打开。宽 640px, 顶部 80px, 背景 canvas, 12px 圆角, floating shadow。结果按标题、正文匹配、操作分组。上下箭头移动, Enter 跳转。

### Status

状态点 8px, 简单直接:

- published: success
- draft: ink-subtle
- archived: danger

badge 默认用 pill, 背景 surface-soft。只有非常重要的新状态才用 `badge-primary`。

## Motion & Interaction

### Claude Visual, Apple Motion

视觉跟 Claude, 交互节奏参考 Apple:

- **按钮按压**: 所有 button 和 icon button pressed 使用 `transform: scale(0.97)`。
- **粘性导航**: 顶部栏和必要的发布操作栏使用 backdrop blur, 避免重阴影。
- **锚点跳转**: TOC 点击平滑滚动, scroll offset 等于 top nav 高度 + 24px。
- **页面跳转**: 路由切换控制在 420ms 内, 内容轻微 fade + translateY 8px。不要做夸张转场。
- **滚动揭示**: 只用于大型 section, opacity 0.01 到 1, translateY 12px 到 0。后台列表不做入场动画。
- **抽屉和搜索**: 从右侧或顶部轻入, 320ms ease-out。

### Keyboard

| 快捷键 | 行为 |
|---|---|
| `⌘K` / `Ctrl+K` | 打开搜索 |
| `⌘S` / `Ctrl+S` | 编辑模式保存 |
| `Esc` | 关闭搜索、抽屉、模态 |
| `Enter` | 激活当前选中项或提交主操作 |
| `Tab` / `Shift+Tab` | 正常焦点移动 |

### Reduced Motion

必须响应 `prefers-reduced-motion`:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }

  .route-enter,
  .section-reveal {
    opacity: 1;
    transform: none;
  }
}
```

## Navigation & Page Flow

### Public Document Flow

公开文档只做阅读:

1. 打开 `/d/<slug>`。
2. 页面在 canvas 上显示文档标题、meta、正文。
3. 文内目录如果需要, 在桌面端作为右侧 TOC; 移动端折叠成顶部 `目录` 按钮。
4. 点击 TOC 平滑跳转到对应 section。
5. 页脚只显示更新时间和必要版权信息。

### Admin Flow

后台默认像 Claude Docs:

1. 顶栏提供全局搜索和账户/发布入口。
2. 左侧 sidebar 选择文档。
3. 中央区域编辑或预览。
4. 右侧区域在 `目录 / 版本 / 发布 / AI 日志` 之间切换。
5. 保存、发布、还原等主操作在用户上下文附近出现, 不做固定大 CTA。

### Apple-inspired Jump Behavior

- 点击导航不立即闪屏, 当前内容先保持, 新内容在 120ms 后淡入。
- 返回列表时恢复之前的滚动位置。
- 重要配置页面可以使用底部 sticky action bar, 背景为 translucent canvas, 但只在操作确实跨越长页面时使用。
- 锚点跳转后, 目标标题不要被顶栏遮住。

## Do's and Don'ts

### Do

- 使用 `#faf9f5` 作为 body 底色, 保持 Claude 式暖白。
- 使用 `#cc785c` 作为唯一主行动色。
- 用 96px section rhythm 和 24px 到 32px 内边距制造呼吸感。
- 公开阅读页保持 760px 内容宽度, 不做宽屏铺满。
- 后台采用 Claude Docs 式 sidebar + main + toc, 但线条要极淡。
- 让按钮、输入框、标题格式都引用 token, 不硬编码。
- 使用暗色代码块承载命令、日志和 diff 预览。
- 使用 Apple 式 pressed scale、sticky blur、平滑锚点跳转。

### Don't

- 不再使用深森林绿和金色作为品牌语言。
- 不使用顶部金色阅读进度条。
- 不给每个 section 或卡片画边框。
- 不用白底卡片浮在米色背景上的 CMS 模板感。
- 不用渐变、装饰光斑、彩色插画堆砌。
- 不在公开阅读页显示登录、编辑、分享、点赞、阅读量。
- 不给普通卡片、按钮和标题加阴影。
- 不在编辑器里开放字体、字号、颜色选择。
- 不用 emoji 当 UI 控件。

## Responsive Behavior

| Breakpoint | Width | 行为 |
|---|---:|---|
| Desktop | ≥ 1100px | 三栏 shell: sidebar + main + toc |
| Tablet | 768-1099px | sidebar 可折叠, toc 隐藏或进入顶部目录按钮 |
| Mobile | < 768px | 单栏阅读, 顶部轻导航, 编辑入口禁用 |

移动端规则:

- 内容左右 padding 20px。
- h1 从 44px 降到 34px, h2 从 32px 降到 26px。
- section padding 从 96px 降到 64px。
- 搜索 overlay 占满宽度, 顶部贴近 nav, 圆角可降到 0。
- 抽屉变成底部 sheet 或 `100vw` 宽面板。
- 所有可点击元素最小 44px 高。

移动端编辑仍然禁用, 显示简短提示: `请在桌面端编辑此文档`。

## Accessibility

### Contrast

目标是 WCAG AA:

| 组合 | 用途 |
|---|---|
| `ink` on `canvas` | 标题 |
| `ink-body` on `canvas` | 正文 |
| `ink-muted` on `canvas` | meta |
| `on-primary` on `primary` | 主按钮 |
| `ink-on-dark` on `surface-dark` | 代码块 |

`ink-subtle` 不能用于正文, 只用于 placeholder、禁用态、非关键时间戳。

### Focus

- 所有交互元素必须键盘可达。
- 不允许裸 `outline: none`。
- focus ring 统一使用 `{shadow.focus}`。
- 图标按钮必须有 `aria-label`。
- 表单控件必须绑定可见或程序化 label。

### Content Semantics

- 文档标题只能有一个 h1。
- section 用 h2, 子节用 h3。
- 表格必须有表头。
- 代码块提供复制按钮时, 按钮文案变化要通过 aria-live 或 toast 告知。

## Implementation Guide

1. 所有颜色、字号、圆角、间距写入 CSS variables, 从本文 token 生成。
2. 先实现 public reader, 再实现 admin shell。公开阅读页是品牌基准。
3. 默认不要创建 card 组件。先问这个内容是否可以作为普通 section 或 soft surface。
4. 新增组件必须定义 default、hover、focus、pressed、disabled, 即使部分状态视觉相同。
5. AI 生成文档模板只允许使用本文定义的 content class: `article-shell`, `info-callout`, `content-card`, `code-block`, `table`。
6. 后台编辑能力只改变内容, 不改变视觉风格。禁止内联 style、自由颜色和自由字号。
7. 修改 token 后同步更新实际样式文件, 保证设计文档和代码不分叉。

## Known Gaps

- **暗色模式** 暂不做。品牌核心是 Claude 式暖白 canvas, 暗色只用于代码和产品 chrome。
- **图标系统** 建议使用 Lucide 线性图标, stroke 1.75px 到 2px, 不使用彩色图标。
- **打印样式** 需要后续定义: 隐藏 nav、sidebar、按钮、toast, canvas 转白, 正文字号略缩。
- **空状态插图** 暂不定义插图风格。优先用 display 标题、一段 muted 文案和一个 primary button。
- **代码高亮** 需要在实现时单独校准, 但必须保持暗色 surface, 不引入高饱和主题。

## References

- Claude Code Docs overview: https://code.claude.com/docs/en/overview
- Apple homepage interaction reference: https://www.apple.com/
- Local reference files: `claude-DESIGN.md`, `apple-DESIGN.md`, `PRODUCT.md`

---

*本文档随设计 token 同步演进。任何 token 增删改先更新此文档, 再改代码。*

# cli-trans

英汉命令行翻译工具。

## 项目简介

一个简洁高效的命令行翻译工具，支持多词典源并行查询、交互式 REPL 模式、生词本管理、缓存历史记录和彩色词性显示。

## 业务价值

### 解决的问题

- **终端用户查词效率低** — 查一个单词需要打开浏览器、访问词典网站、输入单词，至少 5 步操作。`cli-trans` 一步完成。
- **单一词典源不全面** — 有道的中文释义适合入门，牛津的英英释义更精准，柯林斯的例句更丰富。多源合并覆盖不同学习阶段的需求。
- **重复查询浪费网络** — SQLite 缓存避免同一个词的重复网络请求，离线可查历史记录。

### 目标用户

- 程序员（终端高频使用者，不想离开命令行）
- 英语学习者（需要多词典交叉验证释义）
- 学生/研究者（快速查词，积累生词本）

### 核心差异化

| 对比项 | 浏览器查词 | 有道桌面端 | GPT 翻译 | **cli-trans** |
|--------|-----------|-----------|---------|-------------|
| 操作步骤 | 5+ 步 | 3 步 | 2 步 | **1 条命令** |
| 响应速度 | 3-8s | 2-5s | 5-15s | **0.3-1.5s** |
| 词典源 | 1 个 | 1 个 | 1 个 | **5 个并查** |
| 生词管理 | 无 | 有 | 无 | **有** |
| 离线缓存 | 无 | 部分 | 无 | **本地 SQLite** |
| 终端集成 | 无 | 无 | 无 | **原生支持** |

## 技术实现

### 数据流

```
请求 → cache lookup → 命中 → 缓存返回
                    → 未命中 → ThreadPoolExecutor 并发抓取 5 个源
                              → as_completed 逐条 yield (name, result)
                              → 到达即 print + 缓存第一个有结果的源
```

### 架构总览

```
用户输入 (CLI 参数 / REPL 输入流)
       │
       ▼
  ┌─────────────┐     ┌──────────────────┐
  │ __init__.py  │────▶│   translator.py   │─── 并行 HTTP 请求 ──▶ 有道/牛津/柯林斯/剑桥/FreeDict
  │ (CLI 入口)   │     │ (翻译引擎+适配器)  │◀── 0.6s 超时静默跳过 ──┘
  └──────┬──────┘     └────────┬─────────┘
         │                     │ yield (name, result) 逐条流式输出
         │                     ▼
         │              ┌────────────┐
         │              │ formatter.py│─── colorama 着色输出（词性/词典源双色）
         │              └────────────┘
         │
         ├──▶ storage.py ─── SQLite ─── history 表 + vocab 表
         │     (缓存层)         │
         │                      └── ~/.cli-translate.db
         │
         └──▶ repl.py ─── readline ─── 交互循环 + 命令解析
               (REPL 模式)     │
                              └── ~/.cli-trans-repl-history
```

### 项目结构

```text
cliTranslate/
├── cli_trans/              # 主包目录
│   ├── __init__.py         # CLI 入口和参数解析（145 行）
│   ├── __main__.py         # 入口点
│   ├── formatter.py        # 格式化输出，词性/词典源双色区分（129 行）
│   ├── translator.py       # 翻译引擎：统一接口 + 5 个词典适配器（251 行）
│   ├── storage.py          # 数据库层：缓存 + 生词本 CRUD（98 行）
│   └── repl.py             # REPL 交互模式（190 行）
├── tests/                  # 5 个测试文件，51 个测试用例
├── pyproject.toml          # 项目配置
└── README.md               # 说明文档
```

### 技术栈

| 技术 | 用途 |
|------|------|
| Python 3.8+ | 编程语言 |
| requests + Session | HTTP 连接复用，并行抓取 5 个词典 |
| beautifulsoup4 | HTML 解析，提取翻译结果 |
| colorama | 终端 ANSI 彩色输出 |
| sqlite3 | 本地数据库，缓存历史记录和生词本 |
| readline | REPL 交互模式的历史和行编辑 |
| ThreadPoolExecutor | 并发请求 5 个词典源 |
| pytest | 单元测试（51 个测试用例） |

### 核心模块设计

#### translator.py — 翻译引擎

`BaseTranslator` 抽象基类定义了统一接口，5 个子类各自实现具体的 HTML 解析逻辑：

- `YoudaoTranslator` — 解析有道词典的 `.trans-container` / `.simple` 容器
- `OxfordTranslator` — 解析牛津词典的 `.entry .def` 结构
- `CollinsTranslator` — 解析柯林斯词典的 `.hom .def` 结构
- `CambridgeTranslator` — 解析剑桥词典的 `.pr.entry-body__el .def` 结构
- `FreeDictionaryTranslator` — 解析 FreeDict 的 `.pseg .dsingle` 结构

`MultiTranslator.translate()` 是一个生成器，用 `ThreadPoolExecutor` 并发发起请求，通过 `as_completed` 逐条 `yield` 完成的结果。

```python
def translate(self, word, sources=None):
    sources = sources or self.available_sources
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(self._sources[name].translate, word): name
            for name in sources if name in self._sources
        }
        for future in as_completed(futures):
            try:
                result = future.result()
                if result.meanings:
                    yield name, result
            except Exception:
                pass
```

#### storage.py — 数据库层

封装 SQLite 操作，两个核心表：

- `history` 表：`(word, translation, translation_raw, created_at)` — 翻译缓存和历史记录
- `vocab` 表：`(word, added_at, mastered)` — 生词本

#### formatter.py — 格式化输出

- 10 种词性各有独立颜色（`n.` 青色、`v.` 红色、`adj.` 绿色等）
- 5 个词典源各有独立颜色（`[YOUDAO]` 青色、`[OXFORD]` 绿色等）
- `format_single_source()` 格式化单个源的结果，用于流式输出

#### repl.py — 交互模式

基于标准库 `readline` 实现的交互式循环，无需额外依赖。支持：

- 上下方向键翻历史输入
- `/save` `/list` `/history` `/source` 等命令
- `.` 前缀翻译整句
- `Ctrl+D` / `exit` 退出

### 关键技术决策

1. **`ThreadPoolExecutor` 并行请求** — 5 个词典源并发抓取，总耗时 ≈ 最慢的源而非各源之和
2. **生成器流式输出** — `translate()` 用 `yield` 逐条吐出结果，到达即打印，不等全部完成
3. **0.6s 硬超时** — 超过 0.6 秒无响应的源直接跳过，不阻塞、不显示错误
4. **`requests.Session` 连接复用** — `BaseTranslator.__init__` 创建 session，避免重复 TCP/TLS 握手
5. **BS4 + 双模式解析** — BeautifulSoup 解析 HTML，主模式 + 备用模式兜底，容错性强
6. **`beautifulsoup4` 替代正则** — 0.2.0 版本用 BS4 替换了原有的正则 HTML 解析，消除了结构变动导致的断裂风险

## 词典源

- 有道词典 (Youdao) — 英中双语释义
- 牛津词典 (Oxford) — 权威英英释义
- 柯林斯词典 (Collins) — 例句丰富
- 剑桥词典 (Cambridge) — 适合学习者
- FreeDictionary — 免费开源词典

## 功能

1. 多词典源并行查询，结果逐条流式输出；
2. 交互式 REPL 模式（`-i`），支持 `/save` `/list` 等命令；
3. 生词本管理（添加、删除、列表、标记已掌握）；
4. SQLite 缓存，首次在线查询，后续本地秒回；
5. 不同词性使用不同颜色区分，词典源也有独立颜色标识；
6. 所有历史查询记录展示和清除。

## 安装

```bash
pip install cli-trans
```

## 使用

```bash
# 翻译单词（查询所有词典源）
cli-trans hello
cli-trans hello world

# 指定词典源
cli-trans hello --source youdao
cli-trans hello --source youdao,oxford

# 查看历史记录
cli-trans -l
cli-trans -l -n 20

# 强制从 API 重新获取（忽略缓存）
cli-trans hello --force

# 清除历史记录
cli-trans -c

# 进入 REPL 交互模式
cli-trans -i

# 生词本管理
cli-trans --vocab-add hello
cli-trans --vocab-list
cli-trans --vocab-rm hello

# 查看版本
cli-trans -v
```

## REPL 模式命令

| 命令 | 说明 |
|------|------|
| `/save <word>` | 添加单词到生词本 |
| `/remove <word>` | 删除生词 |
| `/list` | 生词本列表 |
| `/history [n]` | 查看翻译历史 |
| `/source [name]` | 切换词典源 |
| `/clear` | 清屏 |
| `/help` | 帮助 |
| `exit` / `Ctrl+D` | 退出 |

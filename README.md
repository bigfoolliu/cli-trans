# cli-trans

英汉命令行翻译工具。

## 项目简介

一个简洁高效的命令行翻译工具，支持多词典源、交互式 REPL 模式、生词本管理、缓存历史记录和彩色词性显示。

## 技术栈

| 技术 | 用途 |
|------|------|
| Python 3.8+ | 编程语言 |
| requests | HTTP 请求，抓取多个词典网页 |
| beautifulsoup4 | HTML 解析，提取翻译结果 |
| colorama | 终端彩色输出（词性和词典源区分） |
| sqlite3 | 本地数据库，存储翻译缓存、历史记录和生词本 |
| readline | REPL 交互模式的历史和行编辑 |

## 项目架构

```text
cliTranslate/
├── cli_trans/              # 主包目录
│   ├── __init__.py         # CLI 入口和参数解析
│   ├── __main__.py         # 入口点
│   ├── formatter.py        # 格式化输出（词性颜色、多源分组）
│   ├── translator.py       # 翻译引擎（统一接口 + 5 个词典适配器）
│   ├── storage.py          # 数据库层（缓存 + 生词本 CRUD）
│   └── repl.py             # 交互式 REPL 模式
├── tests/                  # 单元测试
├── pyproject.toml          # 项目配置
└── README.md               # 说明文档
```

## 词典源

- 有道词典 (Youdao) — 英中双语释义
- 牛津词典 (Oxford) — 权威英英释义
- 柯林斯词典 (Collins) — 例句丰富
- 剑桥词典 (Cambridge) — 适合学习者
- FreeDictionary — 免费开源词典

## 功能

1. 多词典源同时查询，结果按源分组彩色展示；
2. 交互式 REPL 模式（`-i`）；
3. 生词本管理（添加、删除、列表、标记已掌握）；
4. 缓存功能，首次查询在线获取，后续本地查询；
5. 不同词性使用不同颜色区分；
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

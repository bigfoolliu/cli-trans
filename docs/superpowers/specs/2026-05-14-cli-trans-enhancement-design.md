# cli-trans 功能增强设计方案

## 概述

在现有英汉命令行翻译工具基础上，进行三项核心增强：多词典源支持、交互式 REPL 模式、生词本管理。

## 模块架构

```
cli_trans/
├── __init__.py      # 包入口，main() CLI 解析
├── __main__.py      # 不变
├── formatter.py     # 已有 - 格式化输出
├── translator.py    # 翻译引擎 - 统一接口 + 各词典适配器
├── storage.py       # 数据库层 - 缓存 + 生词本 CRUD
└── repl.py          # 交互式 REPL 模式
```

## 翻译引擎设计

### 统一数据结构

```python
@dataclass
class TranslationResult:
    word: str
    source: str          # "youdao" / "oxford" / "collins" / "cambridge" / "freedict"
    meanings: list[Meaning]
    phonetic: str = ""   # 音标
    raw: str = ""        # 纯文本版本
```

### 适配器接口

```python
class BaseTranslator(ABC):
    @abstractmethod
    def translate(self, word: str) -> TranslationResult: ...
    @property
    def name(self) -> str: ...
```

每个词典源实现 `BaseTranslator`，内部用 BeautifulSoup 解析各自的 HTML 结构。

### 核心协调器

```python
class MultiTranslator:
    def __init__(self):
        self.sources = [YoudaoTranslator(), OxfordTranslator(), CollinsTranslator(), ...]

    def translate(self, word: str, sources: list[str] | None = None) -> list[TranslationResult]
```

### 词典源列表

| 源 | 语言 | 特点 |
|----|------|------|
| 有道词典 (Youdao) | 英→中 | 已有的汉化释义 |
| 牛津词典 (Oxford) | 英→英 | 权威英英释义，词源 |
| 柯林斯词典 (Collins) | 英→英 | 例句丰富，同义词 |
| 剑桥词典 (Cambridge) | 英→英→中 | 双语，适合学习者 |
| FreeDictionary | 英→英 | 免费开源，释义简洁 |

### 结果展示

多个源同时查询时，按源分组全部显示，标明来源：
```
hello:
[有道] int. 喂，你好；n. 招呼
[牛津] exclamation: used as a greeting
[柯林斯] CONVENTION: You say 'Hello' when you greet someone
```

## REPL 交互模式

### 触发方式

- `cli-trans`（无参数）进入 REPL
- `cli-trans -i` / `cli-trans --interactive` 显式进入

### 交互设计

```
>>> hello                             ← 输入单词
[有道] int. 喂，你好；n. 招呼，问候
[牛津] ...

>>> /save hello                       ← 标记加入生词本
✅ 已加入生词本

>>> /list                             ← 查看生词本
1. hello       2026-05-14
2. python      2026-05-13

>>> /history                          ← 查看翻译历史

>>> /source oxford                    ← 临时切换只查牛津

>>> .Hello world                      ← 翻译句子

>>> exit / Ctrl+D / Ctrl+C            ← 退出
```

### REPL 命令

| 命令 | 参数 | 说明 |
|------|------|------|
| /save | \<word\> | 添加生词 |
| /remove | \<word\> | 删除生词 |
| /list | - | 生词列表 |
| /history | [n] | 翻译历史（n 为条数） |
| /source | \<name\> | 切换词典源 |
| /help | - | 帮助 |
| /clear | - | 清屏 |
| exit | - | 退出（Ctrl+D/Ctrl+C 均可） |

### 实现方案

基于 Python 标准库 `readline`，无需额外依赖。

## 生词本设计

### 数据存储

复用 `~/.cli-translate.db`，新增表：

```sql
CREATE TABLE IF NOT EXISTS vocab (
    word TEXT PRIMARY KEY,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    mastered INTEGER DEFAULT 0
)
```

### storage.py 接口

- `VocabStore.add(word)` — 加入生词
- `VocabStore.remove(word)` — 删除
- `VocabStore.mark_mastered(word)` — 标记已掌握
- `VocabStore.list(mastered=None) -> list` — 列表
- `VocabStore.is_vocab(word) -> bool` — 是否已加入

### CLI 命令

| 命令 | 说明 |
|------|------|
| `cli-trans --vocab-add hello` | 添加生词 |
| `cli-trans --vocab-list` | 生词列表 |
| `cli-trans --vocab-rm hello` | 删除生词 |

## CLI 接口变更

### 新增参数

| 参数 | 作用 |
|------|------|
| `-i` / `--interactive` | 进入 REPL 模式 |
| `--source` | 指定词典源，如 `--source youdao,oxford` |
| `--vocab-add WORD` | 添加生词 |
| `--vocab-list` | 生词列表 |
| `--vocab-rm WORD` | 删除生词 |

### 保留参数

`-l`, `-n`, `-c`, `-f`, `-v` 保持不变。

## 数据流

```
用户输入 → CLI 解析 / REPL 循环
         → MultiTranslator.translate(word)
           → 各适配器并行请求
           → 解析 HTML → TranslationResult
         → storage.CacheStore 读写（缓存）
         → formatter 格式化（按源分组输出）
         → storage.VocabStore 读写（生词本）
```

## 错误处理

- 网络异常：单个词典源超时不阻塞其他源，该源标记为"不可用"
- 解析失败：该源跳过，不影响其他源结果
- 全部失败：提示"所有词典源均不可用"

## 依赖变化

新增 `beautifulsoup4`（已添加），无其他外部依赖。REPL 使用标准库 `readline`。

# cli-trans

英汉命令行翻译工具。

## 项目简介

一个简洁高效的命令行翻译工具，支持英汉互译，缓存历史记录，彩色词性显示。

## 技术栈

| 技术 | 用途 |
|------|------|
| Python 3.8+ | 编程语言 |
| requests | HTTP 请求，抓取有道词典网页 |
| colorama | 终端彩色输出 |
| sqlite3 | 本地数据库，存储翻译缓存和历史记录 |
| re (正则) | 解析 HTML 网页，提取翻译结果 |
| argparse | 命令行参数解析 |

## 项目架构

```text
cliTranslate/
├── cli_trans/              # 主包目录
│   ├── __init__.py         # 核心逻辑
│   ├── __main__.py         # 入口点
│   └── formatter.py        # 格式化输出
├── pyproject.toml          # 项目配置
├── requirements.txt        # 依赖
└── README.md               # 说明文档
```

## 功能

1. 单个或多个单词同时翻译；
2. 缓存功能，首次查询是在线查询，后续单词查询本地查询，且有标识区分；
3. 不同的词性使用不同的颜色区分；
4. 能将所有历史查询的单词展示。

## 安装

```bash
pip install cli-trans
```

## 使用

```bash
# 翻译单词
cli-trans hello
cli-trans hello world python

# 查看历史记录
cli-trans -l
cli-trans -l -n 20

# 强制从 API 重新获取（忽略缓存）
cli-trans hello --force
cli-trans -f hello

# 清除历史记录
cli-trans -c

# 查看版本
cli-trans -v
```

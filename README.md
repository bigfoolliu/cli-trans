# cli-trans

命令行单词翻译工具。

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

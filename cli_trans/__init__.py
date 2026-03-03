import argparse
import requests
import re
import sqlite3
import os
import json
import sys
from typing import Optional
from urllib.parse import quote
from datetime import datetime

# 启用颜色输出
os.environ.setdefault("FORCE_COLOR", "1")

from colorama import init
from .formatter import format_translation, format_history_item

init(autoreset=True)

VERSION = "0.1.1"

# 数据库路径：用户主目录
DB_PATH = os.path.expanduser("~/.cli-translate.db")


def init_db() -> None:
    """初始化数据库和表"""
    with sqlite3.connect(DB_PATH) as conn:
        # 创建表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                word TEXT PRIMARY KEY,
                translation TEXT NOT NULL,
                translation_raw TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 添加索引
        conn.execute("CREATE INDEX IF NOT EXISTS idx_history_created_at ON history(created_at)")

        # 检查并添加 translation_raw 列（迁移旧数据）
        cursor = conn.execute("PRAGMA table_info(history)")
        columns = [row[1] for row in cursor.fetchall()]
        if "translation_raw" not in columns:
            conn.execute("ALTER TABLE history ADD COLUMN translation_raw TEXT")


def get_from_history(word: str) -> Optional[tuple]:
    """从历史记录查询翻译，返回 (translation, translation_raw, created_at)"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "SELECT translation, translation_raw, created_at FROM history WHERE word = ?",
            (word.lower(),)
        )
        return cursor.fetchone()


def save_to_history(word: str, translation: str, translation_raw: str = None) -> None:
    """保存翻译结果到历史记录"""
    local_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO history (word, translation, translation_raw, created_at) VALUES (?, ?, ?, ?)",
            (word.lower(), translation, translation_raw, local_time)
        )


def list_history(limit: int = 10) -> list:
    """列出历史记录"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "SELECT word, translation, created_at FROM history ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        return cursor.fetchall()


def clear_history() -> int:
    """清除所有历史记录，返回删除的行数"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM history")
        count = cursor.fetchone()[0]
        conn.execute("DELETE FROM history")
        return count


def is_translation_success(result: str) -> bool:
    """判断翻译是否成功"""
    error_keywords = ["未找到", "无法", "超时", "失败"]
    return not any(keyword in result for keyword in error_keywords)


def parse_translation(html: str) -> dict:
    """
    解析有道词典网页，返回结构化数据
    返回: {"word": "hello", "meanings": [{"pos": "int.", "definitions": [...]}, ...], "raw": "原始文本"}
    """
    result = {"word": "", "meanings": [], "raw": ""}

    # 尝试主模式
    pattern = r'<div class="trans-container">\s*<ul>(.*?)</ul>'
    match = re.search(pattern, html, re.DOTALL)

    if match:
        ul_content = match.group(1)
        # 提取每个 li
        items = re.findall(r'<li>(.*?)</li>', ul_content, re.DOTALL)

        for item in items[:10]:
            # 清理 HTML
            text = re.sub(r'<[^>]+>', '', item).strip()
            if not text:
                continue

            # 解析词性和释义
            # 格式: "int. 喂，你好（用于问候或打招呼）"
            pos_match = re.match(r'^([a-z]+\.)\s*(.*)', text, re.IGNORECASE)

            if pos_match:
                pos = pos_match.group(1)
                definition = pos_match.group(2)

                # 查找或创建 meaning
                meaning = None
                for m in result["meanings"]:
                    if m["pos"] == pos:
                        meaning = m
                        break

                if meaning:
                    meaning["definitions"].append(definition)
                else:
                    result["meanings"].append({
                        "pos": pos,
                        "definitions": [definition]
                    })

    # 备用模式
    if not result["meanings"]:
        simple_pattern = r'<div class="simple">(.*?)</div>'
        simple_match = re.search(simple_pattern, html, re.DOTALL)

        if simple_match:
            simple_content = simple_match.group(1)
            p_pattern = r'<p class="(wordGroup|paraphrase)">(.*?)</p>'
            p_matches = re.findall(p_pattern, simple_content, re.DOTALL)

            for _, content in p_matches[:10]:
                text = re.sub(r'<[^>]+>', '', content).strip()
                if not text:
                    continue

                pos_match = re.match(r'^([a-z]+\.)\s*(.*)', text, re.IGNORECASE)

                if pos_match:
                    pos = pos_match.group(1)
                    definition = pos_match.group(2)

                    meaning = None
                    for m in result["meanings"]:
                        if m["pos"] == pos:
                            meaning = m
                            break

                    if meaning:
                        meaning["definitions"].append(definition)
                    else:
                        result["meanings"].append({
                            "pos": pos,
                            "definitions": [definition]
                        })

    # 生成 raw 文本（用于无颜色输出）
    if result["meanings"]:
        raw_parts = []
        for meaning in result["meanings"]:
            pos = meaning["pos"]
            definitions = "；".join(meaning["definitions"])
            raw_parts.append(f"{pos} {definitions}")
        result["raw"] = "\n".join(raw_parts)

    return result


def translate(word: str) -> tuple[str, str]:
    """
    从有道词典网页抓取翻译结果
    返回: (formatted_output, raw_json)
    """
    encoded_word = quote(word)
    url = f"https://dict.youdao.com/w/eng/{encoded_word}/"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        # 解析结构化数据
        data = parse_translation(response.text)
        data["word"] = word.lower()

        if data["meanings"]:
            # 有结构化数据
            formatted = format_translation(data, use_color=True)
            raw_json = json.dumps(data, ensure_ascii=False)
            return formatted, raw_json
        else:
            # 解析失败，返回原始文本
            return "未找到该词的翻译", ""

    except requests.exceptions.Timeout:
        return "请求超时，请稍后重试", ""
    except requests.exceptions.ConnectionError:
        return "无法连接，请检查网络", ""
    except Exception as e:
        return f"翻译失败: {str(e)}", ""


def translate_word(word: str, force: bool = False) -> tuple[str, bool]:
    """
    翻译单个单词
    返回: (result, is_cached)
    """
    word = word.strip()
    if not word:
        return "请输入要翻译的单词", False

    # 查询缓存（除非 force=True）
    if not force:
        cached = get_from_history(word)
        if cached:
            # 从缓存读取，使用颜色格式化
            translation, translation_raw, _ = cached

            if translation_raw:
                try:
                    data = json.loads(translation_raw)
                    data["word"] = word.lower()
                    formatted = format_translation(data, use_color=True)
                    return formatted, True
                except (json.JSONDecodeError, TypeError):
                    pass

            # 旧数据格式
            return translation, True

    # 调用 API 翻译
    result, raw_json = translate(word)

    # 保存到历史记录
    if is_translation_success(result):
        # 生成无颜色版本用于存储
        if raw_json:
            try:
                data = json.loads(raw_json)
                plain_text = format_translation(data, use_color=False)
                save_to_history(word, plain_text, raw_json)
            except (json.JSONDecodeError, TypeError):
                save_to_history(word, result, raw_json)
        else:
            save_to_history(word, result, raw_json)

    return result, False


def main():
    init_db()

    parser = argparse.ArgumentParser(description=f"英汉命令行翻译工具 v{VERSION}")
    parser.add_argument("words", nargs="*", help="要翻译的单词或短语（多个单词用空格分隔）")
    parser.add_argument("-l", "--list", action="store_true", help="列出历史记录")
    parser.add_argument("-n", "--limit", type=int, default=10, help="历史记录显示数量（默认10）")
    parser.add_argument("-c", "--clear", action="store_true", help="清除所有历史记录")
    parser.add_argument("-f", "--force", action="store_true", help="强制从 API 重新获取，忽略缓存")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {VERSION}")

    args = parser.parse_args()

    # 列出历史记录
    if args.list:
        records = list_history(args.limit)
        if not records:
            print("历史记录为空")
            return
        print(f"{'单词':<15} {'翻译':<30} {'查询时间'}")
        print("-" * 70)
        for word, translation, created_at in records:
            print(format_history_item(word, translation, created_at))
        return

    # 清除历史记录
    if args.clear:
        count = clear_history()
        print(f"已清除 {count} 条历史记录")
        return

    # 翻译
    if not args.words:
        parser.print_help()
        return

    # 批量翻译
    for word in args.words:
        result, is_cached = translate_word(word, args.force)
        prefix = "[缓存]" if is_cached else "[在线]"
        print(f"{word}: {prefix}")
        print(result)
        print()


if __name__ == "__main__":
    main()

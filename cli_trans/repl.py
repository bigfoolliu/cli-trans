import sys
import readline
import os
import json
from typing import Optional

from cli_trans.translator import MultiTranslator
from cli_trans.storage import Storage
from cli_trans.formatter import format_multi_source, format_translation, format_history_item


HISTORY_FILE = os.path.expanduser("~/.cli-trans-repl-history")


class Repl:
    def __init__(self, translator: MultiTranslator, storage: Storage):
        self.translator = translator
        self.storage = storage
        self.current_source: Optional[list[str]] = None
        self._setup_readline()

    def _setup_readline(self):
        try:
            readline.read_history_file(HISTORY_FILE)
        except FileNotFoundError:
            pass
        readline.set_history_length(500)

    def _save_history(self):
        try:
            readline.write_history_file(HISTORY_FILE)
        except OSError:
            pass

    def run(self):
        print("cli-trans REPL 模式 — 输入单词查询，输入 /help 查看命令，Ctrl+D 或 exit 退出")
        while True:
            try:
                line = input(">>> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not line:
                continue

            if line.lower() in ("exit", "quit"):
                break

            if line.startswith("/"):
                self._handle_command(line)
            elif line.startswith("."):
                self._translate_text(line[1:].strip())
            else:
                self._translate_text(line)

        self._save_history()

    def _handle_command(self, cmd_line: str):
        parts = cmd_line.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd in ("/save", "/s"):
            self._cmd_save(arg)
        elif cmd in ("/remove", "/rm"):
            self._cmd_remove(arg)
        elif cmd in ("/list", "/l"):
            self._cmd_list()
        elif cmd in ("/history", "/h"):
            self._cmd_history(arg)
        elif cmd in ("/source", "/src"):
            self._cmd_source(arg)
        elif cmd == "/clear":
            os.system("clear" if os.name == "posix" else "cls")
        elif cmd == "/help":
            self._cmd_help()
        else:
            print(f"未知命令: {cmd}。输入 /help 查看可用命令")

    def _translate_text(self, text: str):
        if not text:
            return
        words = text.split()
        for word in words:
            result, is_cached = self._translate_word(word)
            prefix = "[缓存]" if is_cached else "[在线]"
            print(f"{word}: {prefix}")
            print(result)
            print()

    def _translate_word(self, word: str) -> tuple[str, bool]:
        word = word.strip().lower()
        cached = self.storage.get_cached(word)
        if cached:
            translation, translation_raw, _ = cached
            if translation_raw:
                try:
                    data = json.loads(translation_raw)
                    data["word"] = word
                    return format_translation(data, use_color=True), True
                except (json.JSONDecodeError, TypeError):
                    pass
            return translation, True

        sources = self.current_source
        results = self.translator.translate(word, sources=sources)
        formatted = format_multi_source(results, use_color=True)

        for _, tr in results.items():
            if tr.meanings:
                legacy_data = {
                    "word": word,
                    "meanings": [{"pos": m.pos, "definitions": m.definitions} for m in tr.meanings]
                }
                self.storage.save_cache(
                    word,
                    format_translation(legacy_data, use_color=False),
                    json.dumps(legacy_data, ensure_ascii=False)
                )
                break

        return formatted, False

    def _cmd_save(self, word: str):
        if not word:
            print("用法: /save <单词>")
            return
        self.storage.add_vocab(word)
        print(f"✅ 已加入生词本: {word}")

    def _cmd_remove(self, word: str):
        if not word:
            print("用法: /remove <单词>")
            return
        self.storage.remove_vocab(word)
        print(f"✅ 已从生词本删除: {word}")

    def _cmd_list(self):
        items = self.storage.list_vocab()
        if not items:
            print("生词本为空")
            return
        print(f"{'单词':<15} {'加入时间':<20} {'状态'}")
        print("-" * 50)
        for word, added_at, mastered in items:
            status = "✅" if mastered else "📝"
            print(f"{word:<15} {added_at:<20} {status}")

    def _cmd_history(self, limit_str: str):
        limit = int(limit_str) if limit_str.isdigit() else 10
        records = self.storage.list_history(limit)
        if not records:
            print("历史记录为空")
            return
        print(f"{'单词':<15} {'翻译':<30} {'查询时间'}")
        print("-" * 70)
        for word, translation, created_at in records:
            print(format_history_item(word, translation, created_at))

    def _cmd_source(self, source_arg: str):
        available = self.translator.available_sources
        if not source_arg:
            print(f"当前源: {self.current_source or available}")
            print(f"可用源: {', '.join(available)}")
            return
        if source_arg == "all":
            self.current_source = None
            print("已切换为所有源")
        elif source_arg in available:
            self.current_source = [source_arg]
            print(f"已切换为仅查询: {source_arg}")
        else:
            print(f"不可用源: {source_arg}。可用: {', '.join(available)}")

    def _cmd_help(self):
        print("""
可用命令:
  /save <word>      添加到生词本
  /remove <word>    从生词本删除
  /list             生词本列表
  /history [n]      翻译历史（n 为条数）
  /source [name]    查看/切换词典源
  /clear            清屏
  /help             显示此帮助
  exit / Ctrl+D     退出

普通输入直接翻译单词或短语
.开头翻译整句（如 .Hello world）
""")

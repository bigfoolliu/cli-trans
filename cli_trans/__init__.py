import argparse
import os
import json

os.environ.setdefault("FORCE_COLOR", "1")

from colorama import init
init(autoreset=True)

from cli_trans.translator import MultiTranslator
from cli_trans.storage import Storage
from cli_trans.repl import Repl
from cli_trans.formatter import format_translation, format_multi_source, format_history_item

VERSION = "0.2.0"


def translate_word(
    word: str,
    translator: MultiTranslator,
    storage: Storage,
    force: bool = False,
) -> tuple[str, bool]:
    word = word.strip().lower()
    if not word:
        return "请输入要翻译的单词", False

    if not force:
        cached = storage.get_cached(word)
        if cached:
            translation, translation_raw, _ = cached
            if translation_raw:
                try:
                    data = json.loads(translation_raw)
                    data["word"] = word
                    formatted = format_translation(data, use_color=True)
                    return formatted, True
                except (json.JSONDecodeError, TypeError):
                    pass
            return translation, True

    results = translator.translate(word)
    formatted = format_multi_source(results, use_color=True)

    for _, tr in results.items():
        if tr.meanings:
            legacy_data = {
                "word": word,
                "meanings": [{"pos": m.pos, "definitions": m.definitions} for m in tr.meanings]
            }
            storage.save_cache(
                word,
                format_translation(legacy_data, use_color=False),
                json.dumps(legacy_data, ensure_ascii=False)
            )
            break

    return formatted, False


def main():
    storage = Storage()
    translator = MultiTranslator()

    parser = argparse.ArgumentParser(description=f"英汉命令行翻译工具 v{VERSION}")
    parser.add_argument("words", nargs="*", help="要翻译的单词或短语")
    parser.add_argument("-l", "--list", action="store_true", help="列出历史记录")
    parser.add_argument("-n", "--limit", type=int, default=10, help="历史记录显示数量")
    parser.add_argument("-c", "--clear", action="store_true", help="清除所有历史记录")
    parser.add_argument("-f", "--force", action="store_true", help="强制从 API 重新获取")
    parser.add_argument("-i", "--interactive", action="store_true", help="进入 REPL 交互模式")
    parser.add_argument("--source", type=str, help="指定词典源，逗号分隔")
    parser.add_argument("--vocab-add", type=str, help="添加单词到生词本")
    parser.add_argument("--vocab-list", action="store_true", help="列出生词本")
    parser.add_argument("--vocab-rm", type=str, help="从生词本删除单词")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {VERSION}")

    args = parser.parse_args()

    # --- Vocab commands ---
    if args.vocab_add:
        storage.add_vocab(args.vocab_add)
        print(f"已加入生词本: {args.vocab_add}")
        return

    if args.vocab_list:
        items = storage.list_vocab()
        if not items:
            print("生词本为空")
            return
        print(f"{'单词':<15} {'加入时间':<20} {'状态'}")
        print("-" * 50)
        for word, added_at, mastered in items:
            status = "已掌握" if mastered else "学习中"
            print(f"{word:<15} {added_at:<20} {status}")
        return

    if args.vocab_rm:
        storage.remove_vocab(args.vocab_rm)
        print(f"已从生词本删除: {args.vocab_rm}")
        return

    # --- REPL mode ---
    if args.interactive or (not args.words and not args.list and not args.clear):
        repl = Repl(translator, storage)
        repl.run()
        return

    # --- History ---
    if args.list:
        records = storage.list_history(args.limit)
        if not records:
            print("历史记录为空")
            return
        print(f"{'单词':<15} {'翻译':<30} {'查询时间'}")
        print("-" * 70)
        for word, translation, created_at in records:
            print(format_history_item(word, translation, created_at))
        return

    # --- Clear history ---
    if args.clear:
        count = storage.clear_history()
        print(f"已清除 {count} 条历史记录")
        return

    # --- Translate ---
    if not args.words:
        parser.print_help()
        return

    sources = None
    if args.source:
        sources = [s.strip() for s in args.source.split(",")]

    for word in args.words:
        result, is_cached = translate_word(word, translator, storage, args.force)
        prefix = "[缓存]" if is_cached else "[在线]"
        print(f"{word}: {prefix}")
        print(result)
        print()


if __name__ == "__main__":
    main()

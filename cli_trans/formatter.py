from colorama import Fore, Style, init

# 初始化 colorama（Windows 兼容）
init(autoreset=True)

# 词性颜色映射
POS_COLORS = {
    "n.": Fore.CYAN,       # 名词 - 青色
    "v.": Fore.RED,        # 动词 - 红色
    "adj.": Fore.GREEN,    # 形容词 - 绿色
    "adv.": Fore.YELLOW,   # 副词 - 黄色
    "int.": Fore.MAGENTA,  # 感叹词 - 洋红
    "pron.": Fore.BLUE,    # 代词 - 蓝色
    "num.": Fore.LIGHTBLUE_EX,  # 数词 - 浅蓝
    "prep.": Fore.LIGHTMAGENTA_EX,  # 介词 - 浅洋红
    "conj.": Fore.LIGHTRED_EX,  # 连词 - 浅红
    "aux.": Fore.LIGHTGREEN_EX,  # 助动词 - 浅绿
}


def get_pos_color(pos: str) -> str:
    """获取词性对应的颜色"""
    for key, color in POS_COLORS.items():
        if pos.startswith(key):
            return color
    return Fore.WHITE


def format_translation(data: dict, use_color: bool = True) -> str:
    """
    格式化翻译结果
    data: {"word": "hello", "meanings": [{"pos": "int.", "definitions": [...]}, ...]}
    """
    if not data or not data.get("meanings"):
        return data.get("raw", "") if data.get("raw") else ""

    word = data.get("word", "")
    meanings = data.get("meanings", [])

    lines = []
    for meaning in meanings:
        pos = meaning.get("pos", "")
        definitions = meaning.get("definitions", [])

        if not definitions:
            continue

        # 合并多个意思
        definition_text = "；".join(definitions)

        if use_color:
            color = get_pos_color(pos)
            # 颜色 + 词性 + 原色 + 释义
            line = f"{color}{pos}{Style.RESET_ALL} {definition_text}"
        else:
            line = f"{pos} {definition_text}"

        lines.append(line)

    return "\n".join(lines)


def format_history_item(word: str, translation: str, created_at: str, use_color: bool = False) -> str:
    """格式化历史记录单行"""
    trans_summary = translation[:27] + "..." if len(translation) > 27 else translation

    if use_color:
        return f"{Fore.CYAN}{word:<15}{Style.RESET_ALL} {trans_summary:<30} {created_at}"
    else:
        return f"{word:<15} {trans_summary:<30} {created_at}"

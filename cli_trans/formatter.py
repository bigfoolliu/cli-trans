from colorama import Fore, Style, init

init(autoreset=True)

POS_COLORS = {
    "n.": Fore.CYAN,
    "v.": Fore.RED,
    "adj.": Fore.GREEN,
    "adv.": Fore.YELLOW,
    "int.": Fore.MAGENTA,
    "pron.": Fore.BLUE,
    "num.": Fore.LIGHTBLUE_EX,
    "prep.": Fore.LIGHTMAGENTA_EX,
    "conj.": Fore.LIGHTRED_EX,
    "aux.": Fore.LIGHTGREEN_EX,
}

SOURCE_COLORS = {
    "youdao": Fore.CYAN,
    "oxford": Fore.GREEN,
    "collins": Fore.BLUE,
    "cambridge": Fore.YELLOW,
    "freedict": Fore.MAGENTA,
}


def get_pos_color(pos: str) -> str:
    for key, color in POS_COLORS.items():
        if pos.startswith(key):
            return color
    return Fore.WHITE


def get_source_color(source: str) -> str:
    return SOURCE_COLORS.get(source, Fore.WHITE)


def format_translation(data: dict, use_color: bool = True) -> str:
    if not data or not data.get("meanings"):
        return data.get("raw", "") if data.get("raw") else ""

    meanings = data.get("meanings", [])
    lines = []
    for meaning in meanings:
        pos = meaning.get("pos", "")
        definitions = meaning.get("definitions", [])

        if not definitions:
            continue

        definition_text = "；".join(definitions)

        if use_color:
            color = get_pos_color(pos)
            line = f"{color}{pos}{Style.RESET_ALL} {definition_text}"
        else:
            line = f"{pos} {definition_text}"

        lines.append(line)

    return "\n".join(lines)


def format_multi_source(
    results: dict, use_color: bool = True
) -> str:
    lines = []
    for source_name in ["youdao", "oxford", "collins", "cambridge", "freedict"]:
        result = results.get(source_name)
        if result is None:
            continue
        if not result.meanings and result.raw:
            if use_color:
                color = get_source_color(source_name)
                lines.append(f"{color}[{source_name.upper()}]{Style.RESET_ALL} {result.raw}")
            else:
                lines.append(f"[{source_name.upper()}] {result.raw}")
            continue
        if not result.meanings:
            continue

        source_label = source_name.upper()
        if use_color:
            color = get_source_color(source_name)
            lines.append(f"{color}[{source_label}]{Style.RESET_ALL}")
        else:
            lines.append(f"[{source_label}]")

        if result.phonetic:
            lines.append(f"  /{result.phonetic}/")

        for m in result.meanings:
            pos = m.pos
            definitions = "；".join(m.definitions)
            if use_color:
                pos_color = get_pos_color(pos)
                line = f"  {pos_color}{pos}{Style.RESET_ALL} {definitions}"
            else:
                line = f"  {pos} {definitions}"
            lines.append(line)

        lines.append("")

    return "\n".join(lines).rstrip("\n")


def format_single_source(source_name: str, result, use_color: bool = True) -> str:
    lines = []
    source_label = source_name.upper()
    if use_color:
        color = get_source_color(source_name)
        lines.append(f"{color}[{source_label}]{Style.RESET_ALL}")
    else:
        lines.append(f"[{source_label}]")

    if result.phonetic:
        lines.append(f"  /{result.phonetic}/")

    for m in result.meanings:
        pos = m.pos
        definitions = "；".join(m.definitions)
        if use_color:
            pos_color = get_pos_color(pos)
            line = f"  {pos_color}{pos}{Style.RESET_ALL} {definitions}"
        else:
            line = f"  {pos} {definitions}"
        lines.append(line)

    return "\n".join(lines)


def format_history_item(word: str, translation: str, created_at: str) -> str:
    trans_summary = translation[:27] + "..." if len(translation) > 27 else translation
    return f"{word:<15} {trans_summary:<30} {created_at}"

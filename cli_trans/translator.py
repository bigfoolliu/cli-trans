import requests
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup


@dataclass
class Meaning:
    pos: str
    definitions: list[str] = field(default_factory=list)


@dataclass
class TranslationResult:
    word: str
    source: str
    meanings: list[Meaning] = field(default_factory=list)
    phonetic: str = ""
    raw: str = ""


def _parse_pos_definition(text: str, meanings: list[Meaning]) -> None:
    pos_match = re.match(r'^([a-z]+\.)\s*(.*)', text, re.IGNORECASE)
    if not pos_match:
        return
    pos = pos_match.group(1)
    definition = pos_match.group(2)
    for m in meanings:
        if m.pos == pos:
            m.definitions.append(definition)
            return
    meanings.append(Meaning(pos=pos, definitions=[definition]))


class BaseTranslator(ABC):
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def translate(self, word: str) -> TranslationResult:
        ...

    def _build_raw(self, meanings: list[Meaning]) -> str:
        parts = []
        for m in meanings:
            parts.append(f"{m.pos} {'；'.join(m.definitions)}")
        return "\n".join(parts)


class YoudaoTranslator(BaseTranslator):
    @property
    def name(self) -> str:
        return "youdao"

    def translate(self, word: str) -> TranslationResult:
        encoded_word = quote(word)
        url = f"https://dict.youdao.com/w/eng/{encoded_word}/"
        try:
            resp = self.session.get(url, timeout=10)
            return self._parse(resp.text, word)
        except requests.exceptions.Timeout:
            return TranslationResult(word=word, source=self.name, raw="请求超时")
        except requests.exceptions.ConnectionError:
            return TranslationResult(word=word, source=self.name, raw="无法连接")
        except Exception as e:
            return TranslationResult(word=word, source=self.name, raw=f"错误: {e}")

    def _parse(self, html: str, word: str) -> TranslationResult:
        result = TranslationResult(word=word.lower(), source=self.name)
        soup = BeautifulSoup(html, "html.parser")
        container = soup.select_one(".trans-container")
        if container:
            ul = container.select_one("ul")
            if ul:
                for li in ul.select("li"):
                    text = li.get_text(strip=True)
                    if text:
                        _parse_pos_definition(text, result.meanings)
        if not result.meanings:
            for tag in soup.select(".simple .wordGroup, .simple .paraphrase"):
                text = tag.get_text(strip=True)
                if text:
                    _parse_pos_definition(text, result.meanings)
        result.raw = self._build_raw(result.meanings)
        return result


class OxfordTranslator(BaseTranslator):
    @property
    def name(self) -> str:
        return "oxford"

    def translate(self, word: str) -> TranslationResult:
        url = f"https://www.oxfordlearnersdictionaries.com/definition/english/{quote(word.lower())}"
        try:
            resp = self.session.get(url, timeout=10)
            return self._parse(resp.text, word)
        except Exception as e:
            return TranslationResult(word=word, source=self.name, raw=f"牛津词典不可用: {e}")

    def _parse(self, html: str, word: str) -> TranslationResult:
        result = TranslationResult(word=word.lower(), source=self.name)
        soup = BeautifulSoup(html, "html.parser")
        for entry in soup.select(".entry"):
            pos_el = entry.select_one(".pos")
            pos = pos_el.get_text(strip=True) if pos_el else ""
            for def_el in entry.select(".def"):
                text = def_el.get_text(strip=True)
                if text:
                    full = f"{pos} {text}" if pos else text
                    _parse_pos_definition(full, result.meanings)
        result.raw = self._build_raw(result.meanings)
        return result


class CollinsTranslator(BaseTranslator):
    @property
    def name(self) -> str:
        return "collins"

    def translate(self, word: str) -> TranslationResult:
        url = f"https://www.collinsdictionary.com/dictionary/english/{quote(word.lower())}"
        try:
            resp = self.session.get(url, timeout=10)
            return self._parse(resp.text, word)
        except Exception as e:
            return TranslationResult(word=word, source=self.name, raw=f"柯林斯词典不可用: {e}")

    def _parse(self, html: str, word: str) -> TranslationResult:
        result = TranslationResult(word=word.lower(), source=self.name)
        soup = BeautifulSoup(html, "html.parser")
        for hom in soup.select(".hom"):
            pos_el = hom.select_one(".pos")
            pos = pos_el.get_text(strip=True) if pos_el else ""
            for def_el in hom.select(".def"):
                text = def_el.get_text(strip=True)
                if text:
                    full = f"{pos} {text}" if pos else text
                    _parse_pos_definition(full, result.meanings)
        result.raw = self._build_raw(result.meanings)
        return result


class CambridgeTranslator(BaseTranslator):
    @property
    def name(self) -> str:
        return "cambridge"

    def translate(self, word: str) -> TranslationResult:
        url = f"https://dictionary.cambridge.org/dictionary/english/{quote(word.lower())}"
        try:
            resp = self.session.get(url, timeout=10)
            return self._parse(resp.text, word)
        except Exception as e:
            return TranslationResult(word=word, source=self.name, raw=f"剑桥词典不可用: {e}")

    def _parse(self, html: str, word: str) -> TranslationResult:
        result = TranslationResult(word=word.lower(), source=self.name)
        soup = BeautifulSoup(html, "html.parser")
        for entry in soup.select(".pr.entry-body__el"):
            pos_el = entry.select_one(".pos")
            pos = pos_el.get_text(strip=True) if pos_el else ""
            for def_el in entry.select(".def"):
                text = def_el.get_text(strip=True)
                if text:
                    full = f"{pos} {text}" if pos else text
                    _parse_pos_definition(full, result.meanings)
        result.raw = self._build_raw(result.meanings)
        return result


class FreeDictionaryTranslator(BaseTranslator):
    @property
    def name(self) -> str:
        return "freedict"

    def translate(self, word: str) -> TranslationResult:
        url = f"https://www.thefreedictionary.com/{quote(word.lower())}"
        try:
            resp = self.session.get(url, timeout=10)
            return self._parse(resp.text, word)
        except Exception as e:
            return TranslationResult(word=word, source=self.name, raw=f"FreeDict不可用: {e}")

    def _parse(self, html: str, word: str) -> TranslationResult:
        result = TranslationResult(word=word.lower(), source=self.name)
        soup = BeautifulSoup(html, "html.parser")
        for pseg in soup.select(".pseg"):
            pos_el = pseg.select_one(".pos")
            pos = pos_el.get_text(strip=True) if pos_el else ""
            for dsingle in pseg.select(".dsingle"):
                text = dsingle.get_text(strip=True)
                if text:
                    full = f"{pos} {text}" if pos else text
                    _parse_pos_definition(full, result.meanings)
        if not result.meanings:
            for def_el in soup.select(".definition"):
                text = def_el.get_text(strip=True)
                if text:
                    _parse_pos_definition(text, result.meanings)
        result.raw = self._build_raw(result.meanings)
        return result


class MultiTranslator:
    def __init__(self):
        self._sources: dict[str, BaseTranslator] = {}
        self._register(YoudaoTranslator())
        self._register(OxfordTranslator())
        self._register(CollinsTranslator())
        self._register(CambridgeTranslator())
        self._register(FreeDictionaryTranslator())

    def _register(self, translator: BaseTranslator) -> None:
        self._sources[translator.name] = translator

    @property
    def available_sources(self) -> list[str]:
        return list(self._sources.keys())

    def translate(
        self, word: str, sources: Optional[list[str]] = None
    ) -> dict[str, TranslationResult]:
        sources = sources or self.available_sources
        results = {}
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self._sources[name].translate, word): name
                for name in sources if name in self._sources
            }
            for future in as_completed(futures):
                name = futures[future]
                try:
                    results[name] = future.result()
                except Exception as e:
                    results[name] = TranslationResult(word=word, source=name, raw=f"错误: {e}")
        return results

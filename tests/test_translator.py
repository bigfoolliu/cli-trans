import pytest
from cli_trans.translator import (
    YoudaoTranslator, TranslationResult, Meaning,
    MultiTranslator, _parse_pos_definition,
)


class TestParsePosDefinition:
    def test_basic_pos(self):
        meanings = []
        _parse_pos_definition("n. 世界，地球", meanings)
        assert len(meanings) == 1
        assert meanings[0].pos == "n."
        assert meanings[0].definitions == ["世界，地球"]

    def test_same_pos_merged(self):
        meanings = []
        _parse_pos_definition("n. 世界", meanings)
        _parse_pos_definition("n. 地球", meanings)
        assert len(meanings) == 1
        assert meanings[0].definitions == ["世界", "地球"]

    def test_different_pos(self):
        meanings = []
        _parse_pos_definition("n. 世界", meanings)
        _parse_pos_definition("v. 运行", meanings)
        assert len(meanings) == 2

    def test_no_pos_prefix(self):
        meanings = []
        _parse_pos_definition("世界", meanings)
        assert len(meanings) == 0


class TestYoudaoTranslator:
    def test_parse_html_main(self):
        html = """
        <div class="trans-container">
            <ul>
                <li><span>n.</span> 世界，地球</li>
                <li><span>v.</span> 运行</li>
            </ul>
        </div>
        """
        t = YoudaoTranslator()
        result = t._parse(html, "world")
        assert result.word == "world"
        assert result.source == "youdao"
        meanings = {(m.pos, tuple(m.definitions)) for m in result.meanings}
        assert ("n.", ("世界，地球",)) in meanings
        assert ("v.", ("运行",)) in meanings

    def test_parse_html_simple_fallback(self):
        html = """
        <div class="simple">
            <p class="wordGroup">n. 喂，你好</p>
        </div>
        """
        t = YoudaoTranslator()
        result = t._parse(html, "hello")
        assert len(result.meanings) > 0
        assert result.raw != ""

    def test_parse_empty(self):
        t = YoudaoTranslator()
        result = t._parse("<html></html>", "test")
        assert len(result.meanings) == 0
        assert result.raw == ""


class TestMultiTranslator:
    def test_default_has_youdao(self):
        mt = MultiTranslator()
        assert "youdao" in mt.available_sources

    def test_translate_yields_results(self):
        mt = MultiTranslator()
        results = list(mt.translate("test"))
        names = [name for name, _ in results]
        assert "youdao" in names

    def test_translate_filtered_sources(self):
        mt = MultiTranslator()
        results = list(mt.translate("test", sources=["youdao"]))
        names = [name for name, _ in results]
        assert "youdao" in names

    def test_translate_yields_only_with_meanings(self):
        mt = MultiTranslator()
        results = list(mt.translate("test"))
        for _, result in results:
            assert len(result.meanings) > 0

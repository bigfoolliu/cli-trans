import pytest
from cli_trans.translator import (
    OxfordTranslator, CollinsTranslator, CambridgeTranslator,
    FreeDictionaryTranslator, MultiTranslator,
)


class TestOxfordTranslator:
    def test_parse_basic(self):
        html = """
        <div class="entry">
            <span class="pos">n.</span>
            <span class="def">a greeting or salutation</span>
        </div>
        """
        t = OxfordTranslator()
        result = t._parse(html, "hello")
        assert result.source == "oxford"
        assert any("greeting" in d for m in result.meanings for d in m.definitions)

    def test_parse_empty(self):
        t = OxfordTranslator()
        result = t._parse("<html></html>", "test")
        assert len(result.meanings) == 0


class TestCollinsTranslator:
    def test_parse_basic(self):
        html = """
        <div class="hom">
            <span class="pos">n.</span>
            <span class="def">a greeting or salutation</span>
        </div>
        """
        t = CollinsTranslator()
        result = t._parse(html, "hello")
        assert result.source == "collins"
        assert any("greeting" in d for m in result.meanings for d in m.definitions)

    def test_parse_empty(self):
        t = CollinsTranslator()
        result = t._parse("<html></html>", "test")
        assert len(result.meanings) == 0


class TestCambridgeTranslator:
    def test_parse_basic(self):
        html = """
        <div class="pr entry-body__el">
            <span class="pos">n.</span>
            <span class="def">a greeting</span>
        </div>
        """
        t = CambridgeTranslator()
        result = t._parse(html, "hello")
        assert result.source == "cambridge"
        assert any("greeting" in d for m in result.meanings for d in m.definitions)

    def test_parse_empty(self):
        t = CambridgeTranslator()
        result = t._parse("<html></html>", "test")
        assert len(result.meanings) == 0


class TestFreeDictionaryTranslator:
    def test_parse_pseg(self):
        html = """
        <div class="pseg">
            <span class="pos">n.</span>
            <div class="dsingle">a greeting</div>
        </div>
        """
        t = FreeDictionaryTranslator()
        result = t._parse(html, "hello")
        assert result.source == "freedict"
        assert any("greeting" in d for m in result.meanings for d in m.definitions)

    def test_parse_fallback_definition(self):
        html = """
        <div class="definition">n. a greeting or salutation</div>
        """
        t = FreeDictionaryTranslator()
        result = t._parse(html, "hello")
        assert len(result.meanings) > 0

    def test_parse_empty(self):
        t = FreeDictionaryTranslator()
        result = t._parse("<html></html>", "test")
        assert len(result.meanings) == 0


class TestMultiTranslatorAllSources:
    def test_all_sources_registered(self):
        mt = MultiTranslator()
        expected = {"youdao", "oxford", "collins", "cambridge", "freedict"}
        assert set(mt.available_sources) == expected

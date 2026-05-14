import pytest
from cli_trans.formatter import (
    format_multi_source, format_translation, format_history_item
)
from cli_trans.translator import TranslationResult, Meaning


class TestFormatMultiSource:
    def test_single_source(self):
        result = TranslationResult(
            word="hello", source="youdao",
            meanings=[Meaning(pos="int.", definitions=["喂，你好"])],
            raw="int. 喂，你好"
        )
        output = format_multi_source({"youdao": result}, use_color=False)
        assert "[YOUDAO]" in output
        assert "int." in output
        assert "喂，你好" in output

    def test_multiple_sources(self):
        yd = TranslationResult(
            word="hello", source="youdao",
            meanings=[Meaning(pos="int.", definitions=["喂，你好"])],
            raw="int. 喂，你好"
        )
        ox = TranslationResult(
            word="hello", source="oxford",
            meanings=[Meaning(pos="n.", definitions=["a greeting"])],
            raw="n. a greeting"
        )
        output = format_multi_source({"youdao": yd, "oxford": ox}, use_color=False)
        assert "[YOUDAO]" in output
        assert "[OXFORD]" in output

    def test_empty_results(self):
        assert format_multi_source({}, use_color=False) == ""

    def test_error_result(self):
        result = TranslationResult(word="test", source="youdao", raw="请求超时")
        output = format_multi_source({"youdao": result}, use_color=False)
        assert "[YOUDAO]" in output
        assert "请求超时" in output

    def test_ordered_by_source(self):
        yd = TranslationResult(
            word="hello", source="youdao",
            meanings=[Meaning(pos="int.", definitions=["喂"])],
            raw="int. 喂"
        )
        ox = TranslationResult(
            word="hello", source="oxford",
            meanings=[Meaning(pos="n.", definitions=["greeting"])],
            raw="n. greeting"
        )
        output = format_multi_source({"oxford": ox, "youdao": yd}, use_color=False)
        assert output.index("[YOUDAO]") < output.index("[OXFORD]")


class TestFormatTranslationLegacy:
    def test_legacy_format(self):
        data = {
            "word": "hello",
            "meanings": [{"pos": "int.", "definitions": ["喂，你好"]}]
        }
        result = format_translation(data, use_color=False)
        assert "int." in result
        assert "喂，你好" in result

    def test_legacy_empty(self):
        assert format_translation({}, use_color=False) == ""


class TestFormatHistoryItem:
    def test_short(self):
        result = format_history_item("hello", "喂，你好", "2026-05-14")
        assert "hello" in result
        assert "喂，你好" in result
        assert "2026-05-14" in result

    def test_long_truncated(self):
        long_trans = "a" * 50
        result = format_history_item("hello", long_trans, "2026-05-14")
        assert "..." in result

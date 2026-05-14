import pytest
from cli_trans.storage import Storage


@pytest.fixture
def store(tmp_path):
    db_path = str(tmp_path / "test.db")
    return Storage(db_path)


class TestCache:
    def test_save_and_get(self, store):
        store.save_cache("hello", "喂，你好", '{"word":"hello"}')
        result = store.get_cached("hello")
        assert result is not None
        assert result[0] == "喂，你好"
        assert result[1] == '{"word":"hello"}'

    def test_get_nonexistent(self, store):
        assert store.get_cached("nonexistent") is None

    def test_list_history(self, store):
        store.save_cache("a", "翻译a")
        store.save_cache("b", "翻译b")
        records = store.list_history(5)
        assert len(records) >= 2

    def test_clear_history(self, store):
        store.save_cache("x", "翻译x")
        assert store.clear_history() >= 1
        assert store.get_cached("x") is None


class TestVocab:
    def test_add_and_list(self, store):
        store.add_vocab("hello")
        store.add_vocab("world")
        items = store.list_vocab()
        words = [item[0] for item in items]
        assert "hello" in words
        assert "world" in words

    def test_remove(self, store):
        store.add_vocab("hello")
        store.remove_vocab("hello")
        assert not store.is_vocab("hello")

    def test_is_vocab(self, store):
        assert not store.is_vocab("hello")
        store.add_vocab("hello")
        assert store.is_vocab("hello")

    def test_mark_mastered(self, store):
        store.add_vocab("hello")
        store.mark_mastered("hello")
        items = store.list_vocab(mastered=True)
        assert any(item[0] == "hello" for item in items)

    def test_case_insensitive(self, store):
        store.add_vocab("Hello")
        assert store.is_vocab("hello")

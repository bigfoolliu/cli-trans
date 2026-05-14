import pytest
from cli_trans.repl import Repl
from cli_trans.translator import MultiTranslator
from cli_trans.storage import Storage


@pytest.fixture
def repl(tmp_path):
    translator = MultiTranslator()
    storage = Storage(str(tmp_path / "test.db"))
    return Repl(translator, storage)


class TestReplCommands:
    def test_handle_save(self, repl):
        repl._handle_command("/save hello")
        assert repl.storage.is_vocab("hello")

    def test_handle_remove(self, repl):
        repl.storage.add_vocab("hello")
        repl._handle_command("/remove hello")
        assert not repl.storage.is_vocab("hello")

    def test_handle_list_empty(self, repl, capsys):
        repl._handle_command("/list")
        captured = capsys.readouterr()
        assert "生词本为空" in captured.out

    def test_handle_history_empty(self, repl, capsys):
        repl._handle_command("/history")
        captured = capsys.readouterr()
        assert "历史记录为空" in captured.out

    def test_handle_unknown_command(self, repl, capsys):
        repl._handle_command("/xyz")
        captured = capsys.readouterr()
        assert "未知命令" in captured.out

    def test_handle_save_no_arg(self, repl, capsys):
        repl._handle_command("/save")
        captured = capsys.readouterr()
        assert "用法" in captured.out

    def test_handle_source_list(self, repl, capsys):
        repl._handle_command("/source")
        captured = capsys.readouterr()
        assert "可用源" in captured.out

    def test_handle_source_switch(self, repl, capsys):
        repl._handle_command("/source youdao")
        captured = capsys.readouterr()
        assert "youdao" in captured.out

    def test_handle_source_invalid(self, repl, capsys):
        repl._handle_command("/source nonexistent")
        captured = capsys.readouterr()
        assert "不可用源" in captured.out

    def test_handle_help(self, repl, capsys):
        repl._handle_command("/help")
        captured = capsys.readouterr()
        assert "/save" in captured.out
        assert "/history" in captured.out

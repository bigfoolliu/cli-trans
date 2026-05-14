import sqlite3
import os
from typing import Optional
from datetime import datetime

DB_PATH = os.path.expanduser("~/.cli-translate.db")


class Storage:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    word TEXT PRIMARY KEY,
                    translation TEXT NOT NULL,
                    translation_raw TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_history_created_at ON history(created_at)")

            cursor = conn.execute("PRAGMA table_info(history)")
            columns = [row[1] for row in cursor.fetchall()]
            if "translation_raw" not in columns:
                conn.execute("ALTER TABLE history ADD COLUMN translation_raw TEXT")

            conn.execute("""
                CREATE TABLE IF NOT EXISTS vocab (
                    word TEXT PRIMARY KEY,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    mastered INTEGER DEFAULT 0
                )
            """)

    # --- Cache methods ---

    def get_cached(self, word: str) -> Optional[tuple]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT translation, translation_raw, created_at FROM history WHERE word = ?",
                (word.lower(),)
            )
            return cursor.fetchone()

    def save_cache(self, word: str, translation: str, translation_raw: str = None) -> None:
        local_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO history (word, translation, translation_raw, created_at) VALUES (?, ?, ?, ?)",
                (word.lower(), translation, translation_raw, local_time)
            )

    def list_history(self, limit: int = 10) -> list:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT word, translation, created_at FROM history ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
            return cursor.fetchall()

    def clear_history(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM history")
            count = cursor.fetchone()[0]
            conn.execute("DELETE FROM history")
            return count

    # --- Vocab methods ---

    def add_vocab(self, word: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO vocab (word) VALUES (?)",
                (word.lower(),)
            )

    def remove_vocab(self, word: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM vocab WHERE word = ?", (word.lower(),))

    def mark_mastered(self, word: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE vocab SET mastered = 1 WHERE word = ?", (word.lower(),))

    def list_vocab(self, mastered: Optional[bool] = None) -> list:
        with sqlite3.connect(self.db_path) as conn:
            if mastered is not None:
                cursor = conn.execute(
                    "SELECT word, added_at, mastered FROM vocab WHERE mastered = ? ORDER BY added_at DESC",
                    (1 if mastered else 0,)
                )
            else:
                cursor = conn.execute(
                    "SELECT word, added_at, mastered FROM vocab ORDER BY added_at DESC"
                )
            return cursor.fetchall()

    def is_vocab(self, word: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM vocab WHERE word = ?", (word.lower(),)
            )
            return cursor.fetchone() is not None

from __future__ import annotations

import json
import os
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class HistoryStoreStatus:
    backend: str
    db_path: str
    ttl_seconds: int
    max_turns: int
    redis_available: bool  # Kept for compatibility formatting


class ConversationHistoryStore:
    """
    SQLite-backed history store for conversation memory and error logging.
    """

    def __init__(self) -> None:
        self.db_path = str(
            Path(__file__).resolve().parent.parent / "artifacts" / "agentic_bi.sqlite"
        )
        self.ttl_seconds = int(os.getenv("SESSION_TTL_SECONDS", "86400"))
        self.max_turns = int(os.getenv("SESSION_MAX_TURNS", "30"))
        self._lock = threading.Lock()
        
        self._init_db()

    def _init_db(self) -> None:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS conversation_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS error_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        error_type TEXT NOT NULL,
                        error_message TEXT NOT NULL,
                        stack_trace TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_history_session ON conversation_history(session_id)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_errors_session ON error_logs(session_id)"
                )

    def status(self) -> HistoryStoreStatus:
        return HistoryStoreStatus(
            backend="sqlite",
            db_path=self.db_path,
            ttl_seconds=self.ttl_seconds,
            max_turns=self.max_turns,
            redis_available=False,
        )

    def get_history(self, session_id: str) -> list[dict[str, str]]:
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """
                    SELECT role, content 
                    FROM conversation_history 
                    WHERE session_id = ? 
                    ORDER BY timestamp ASC
                    """,
                    (session_id,)
                )
                rows = cursor.fetchall()
                
        # Keep only the latest `max_turns` interactions
        turns = [{"role": row["role"], "content": row["content"]} for row in rows]
        return turns[-self.max_turns:] if self.max_turns > 0 else turns

    def append_turns(self, session_id: str, turns: list[dict[str, str]]) -> list[dict[str, str]]:
        sanitized = self._sanitize_turns(turns)
        if not sanitized:
            return self.get_history(session_id)
            
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                for turn in sanitized:
                    conn.execute(
                        """
                        INSERT INTO conversation_history (session_id, role, content)
                        VALUES (?, ?, ?)
                        """,
                        (session_id, turn["role"], turn["content"])
                    )
        
        return self.get_history(session_id)

    def log_error(self, session_id: str, error_type: str, error_message: str, stack_trace: str = "") -> None:
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO error_logs (session_id, error_type, error_message, stack_trace)
                    VALUES (?, ?, ?, ?)
                    """,
                    (session_id, str(error_type), str(error_message), str(stack_trace))
                )

    @staticmethod
    def _sanitize_turns(turns: list[dict[str, Any]]) -> list[dict[str, str]]:
        out: list[dict[str, str]] = []
        for turn in turns:
            role = str(turn.get("role", "")).strip().lower()
            content = str(turn.get("content", "")).strip()
            if role not in {"user", "assistant", "model"}:
                continue
            if not content:
                continue
            normalized_role = "assistant" if role == "model" else role
            out.append({"role": normalized_role, "content": content})
        return out

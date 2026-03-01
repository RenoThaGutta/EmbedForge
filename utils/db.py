from __future__ import annotations

import sqlite3
from contextlib import contextmanager

from config import DB_PATH


@contextmanager
def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS guild_usage (
                guild_id TEXT NOT NULL,
                period_key TEXT NOT NULL,
                embeds_created INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (guild_id, period_key)
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS embed_usage (
                guild_id TEXT NOT NULL,
                channel_id TEXT NOT NULL,
                message_id TEXT NOT NULL,
                edits_used INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (guild_id, message_id)
            )
            """
        )


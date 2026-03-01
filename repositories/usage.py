from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone

from utils.db import get_connection


def current_period_key(now: datetime | None = None) -> str:
    timestamp = now or datetime.now(timezone.utc)
    return timestamp.strftime("%Y-%m")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class UsageRepository(ABC):
    @abstractmethod
    def ensure_period_rollover(self, guild_id: int) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_guild_embeds_created(self, guild_id: int, period_key: str) -> int:
        raise NotImplementedError

    @abstractmethod
    def increment_guild_embeds_created(self, guild_id: int, period_key: str) -> int:
        raise NotImplementedError

    @abstractmethod
    def get_embed_edits_used(self, guild_id: int, message_id: int) -> int:
        raise NotImplementedError

    @abstractmethod
    def increment_embed_edits_used(self, guild_id: int, channel_id: int, message_id: int) -> int:
        raise NotImplementedError

    @abstractmethod
    def ensure_embed_record(self, guild_id: int, channel_id: int, message_id: int) -> None:
        raise NotImplementedError


class SQLiteUsageRepository(UsageRepository):
    def ensure_period_rollover(self, guild_id: int) -> str:
        period_key = current_period_key()
        now = utc_now_iso()
        with get_connection() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO guild_usage (guild_id, period_key, embeds_created, updated_at)
                VALUES (?, ?, 0, ?)
                """,
                (str(guild_id), period_key, now),
            )
        return period_key

    def get_guild_embeds_created(self, guild_id: int, period_key: str) -> int:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT embeds_created
                FROM guild_usage
                WHERE guild_id = ? AND period_key = ?
                """,
                (str(guild_id), period_key),
            ).fetchone()
        return int(row["embeds_created"]) if row else 0

    def increment_guild_embeds_created(self, guild_id: int, period_key: str) -> int:
        now = utc_now_iso()
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO guild_usage (guild_id, period_key, embeds_created, updated_at)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(guild_id, period_key)
                DO UPDATE SET
                    embeds_created = embeds_created + 1,
                    updated_at = excluded.updated_at
                """,
                (str(guild_id), period_key, now),
            )
            row = connection.execute(
                """
                SELECT embeds_created
                FROM guild_usage
                WHERE guild_id = ? AND period_key = ?
                """,
                (str(guild_id), period_key),
            ).fetchone()
        return int(row["embeds_created"]) if row else 0

    def get_embed_edits_used(self, guild_id: int, message_id: int) -> int:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT edits_used
                FROM embed_usage
                WHERE guild_id = ? AND message_id = ?
                """,
                (str(guild_id), str(message_id)),
            ).fetchone()
        return int(row["edits_used"]) if row else 0

    def increment_embed_edits_used(self, guild_id: int, channel_id: int, message_id: int) -> int:
        now = utc_now_iso()
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO embed_usage (guild_id, channel_id, message_id, edits_used, created_at, updated_at)
                VALUES (?, ?, ?, 1, ?, ?)
                ON CONFLICT(guild_id, message_id)
                DO UPDATE SET
                    channel_id = excluded.channel_id,
                    edits_used = edits_used + 1,
                    updated_at = excluded.updated_at
                """,
                (str(guild_id), str(channel_id), str(message_id), now, now),
            )
            row = connection.execute(
                """
                SELECT edits_used
                FROM embed_usage
                WHERE guild_id = ? AND message_id = ?
                """,
                (str(guild_id), str(message_id)),
            ).fetchone()
        return int(row["edits_used"]) if row else 0

    def ensure_embed_record(self, guild_id: int, channel_id: int, message_id: int) -> None:
        now = utc_now_iso()
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO embed_usage (guild_id, channel_id, message_id, edits_used, created_at, updated_at)
                VALUES (?, ?, ?, 0, ?, ?)
                ON CONFLICT(guild_id, message_id)
                DO UPDATE SET
                    channel_id = excluded.channel_id,
                    updated_at = excluded.updated_at
                """,
                (str(guild_id), str(channel_id), str(message_id), now, now),
            )


repository: UsageRepository = SQLiteUsageRepository()


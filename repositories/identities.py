from __future__ import annotations

import json
import shutil
from typing import Optional

from config import IDENTITY_BACKUP_FILE, IDENTITY_FILE
from utils.logging import get_logger

logger = get_logger("repositories.identities")


class JsonIdentityRepository:
    def __init__(self, identity_file=IDENTITY_FILE, backup_file=IDENTITY_BACKUP_FILE):
        self.identity_file = identity_file
        self.backup_file = backup_file

    def load_identity(self, guild_id: int) -> Optional[dict]:
        identities = self._load_all()
        identity = identities.get(str(guild_id))
        return identity if isinstance(identity, dict) else None

    def save_identity(self, guild_id: int, display_name: str, avatar_url: str) -> dict:
        identities = self._load_all()
        data = {
            "display_name": str(display_name).strip(),
            "avatar_url": str(avatar_url).strip(),
        }
        identities[str(guild_id)] = data
        self._write_all(identities)
        return data

    def delete_identity(self, guild_id: int) -> bool:
        identities = self._load_all()
        if str(guild_id) not in identities:
            return False

        del identities[str(guild_id)]
        self._write_all(identities)
        return True

    def _load_all(self) -> dict:
        if not self.identity_file.exists():
            return {}

        try:
            with self.identity_file.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except json.JSONDecodeError:
            logger.exception("Identity store is invalid JSON; attempting backup recovery")
            return self._load_backup()
        except Exception:
            logger.exception("Failed reading identity store")
            return self._load_backup()

        if isinstance(data, dict):
            return data

        logger.warning("Identity store root was not an object; ignoring invalid contents")
        return {}

    def _load_backup(self) -> dict:
        if not self.backup_file.exists():
            return {}

        try:
            with self.backup_file.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception:
            logger.exception("Failed reading identity backup store")
            return {}

        if isinstance(data, dict):
            return data

        logger.warning("Identity backup store root was not an object; ignoring invalid contents")
        return {}

    def _write_all(self, data: dict) -> None:
        self.identity_file.parent.mkdir(parents=True, exist_ok=True)

        if self.identity_file.exists():
            try:
                shutil.copy2(self.identity_file, self.backup_file)
            except Exception:
                logger.exception("Failed to refresh identity backup before write")

        temp_file = self.identity_file.with_suffix(self.identity_file.suffix + ".tmp")
        with temp_file.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
            handle.flush()

        temp_file.replace(self.identity_file)


repository = JsonIdentityRepository()


def load_guild_identity(guild_id: int) -> Optional[dict]:
    return repository.load_identity(guild_id)


def save_guild_identity(guild_id: int, display_name: str, avatar_url: str) -> dict:
    return repository.save_identity(guild_id, display_name, avatar_url)


def delete_guild_identity(guild_id: int) -> bool:
    return repository.delete_identity(guild_id)


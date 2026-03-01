from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("DB_PATH", str(BASE_DIR / "embedforge.sqlite3")))
TEMPLATE_FILE = BASE_DIR / "embed_templates.json"
TEMPLATE_BACKUP_FILE = BASE_DIR / "embed_templates.bak.json"
IDENTITY_FILE = BASE_DIR / "guild_identities.json"
IDENTITY_BACKUP_FILE = BASE_DIR / "guild_identities.bak.json"
MANAGED_WEBHOOK_NAME = "EmbedForge"
DEFAULT_PRO_PURCHASE_URL = "https://discord.com/discovery/applications/1477438235608219980/store/1477551786675146804"
DEFAULT_PRO_DISPLAY_NAME = "EmbedForge Pro"
DEFAULT_PRO_AVATAR_URL = "https://drive.google.com/uc?export=view&id=1N_lKhtG5O4Y0h1z5mLJp5fWjXmRnNrED"


def get_bot_token() -> str:
    token = os.getenv("DISCORD_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Missing DISCORD_BOT_TOKEN environment variable.")
    return token


def get_pro_sku_id() -> int | None:
    raw = os.getenv("EMBEDFORGE_PRO_SKU_ID", "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError("EMBEDFORGE_PRO_SKU_ID must be an integer.") from exc


def get_pro_guild_allowlist() -> set[int]:
    raw = os.getenv("PRO_GUILD_ALLOWLIST", "").strip()
    if not raw:
        return set()

    guild_ids: set[int] = set()
    for part in raw.split(","):
        item = part.strip()
        if not item:
            continue
        try:
            guild_ids.add(int(item))
        except ValueError as exc:
            raise RuntimeError("PRO_GUILD_ALLOWLIST must contain comma-separated guild IDs.") from exc
    return guild_ids


def get_entitlement_cache_seconds() -> int:
    raw = os.getenv("ENTITLEMENT_CACHE_SECONDS", "120").strip()
    try:
        return max(10, int(raw))
    except ValueError as exc:
        raise RuntimeError("ENTITLEMENT_CACHE_SECONDS must be an integer.") from exc


def get_pro_purchase_url() -> str:
    return os.getenv("EMBEDFORGE_PRO_URL", DEFAULT_PRO_PURCHASE_URL).strip()


def get_default_pro_display_name() -> str:
    return os.getenv("EMBEDFORGE_PRO_DISPLAY_NAME", DEFAULT_PRO_DISPLAY_NAME).strip()


def get_default_pro_avatar_url() -> str:
    return os.getenv("EMBEDFORGE_PRO_AVATAR_URL", DEFAULT_PRO_AVATAR_URL).strip()


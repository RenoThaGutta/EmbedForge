from __future__ import annotations

import time

import discord

from config import get_entitlement_cache_seconds, get_pro_guild_allowlist, get_pro_sku_id
from utils.logging import get_logger

logger = get_logger("services.entitlements")
_CACHE: dict[int, tuple[float, bool]] = {}


def invalidate_pro_cache(guild_id: int | None = None) -> None:
    if guild_id is None:
        _CACHE.clear()
        return
    _CACHE.pop(guild_id, None)


async def is_pro_guild(client: discord.Client, guild_id: int | None) -> bool:
    if guild_id is None:
        return False

    if guild_id in get_pro_guild_allowlist():
        return True

    sku_id = get_pro_sku_id()
    if sku_id is None:
        return False

    now = time.monotonic()
    cached = _CACHE.get(guild_id)
    if cached and cached[0] > now:
        return cached[1]

    is_pro = False
    try:
        sku = discord.Object(id=sku_id)
        guild = discord.Object(id=guild_id)
        async for entitlement in client.entitlements(
            limit=100,
            skus=[sku],
            guild=guild,
            exclude_ended=True,
            exclude_deleted=True,
        ):
            if entitlement.guild_id != guild_id:
                continue
            if entitlement.sku_id != sku_id:
                continue
            if entitlement.is_expired():
                continue
            is_pro = True
            break
    except Exception:
        logger.exception("Failed checking guild entitlement for guild_id=%s", guild_id)
        is_pro = False

    _CACHE[guild_id] = (now + get_entitlement_cache_seconds(), is_pro)
    return is_pro


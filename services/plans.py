from __future__ import annotations

from dataclasses import dataclass

import discord

from errors.app_errors import FeatureUnavailableError, PlanLimitError
from repositories.usage import current_period_key, repository as usage_repository
from services.entitlements import is_pro_guild

FREE_EMBED_LIMIT = 5
FREE_EDIT_LIMIT = 1


@dataclass
class PlanStatus:
    is_pro: bool
    period_key: str
    embeds_used: int
    embed_limit: int | None
    edits_used: int | None = None
    edit_limit: int | None = None


async def get_plan_status(client: discord.Client, guild_id: int, message_id: int | None = None) -> PlanStatus:
    pro = await is_pro_guild(client, guild_id)
    period_key = usage_repository.ensure_period_rollover(guild_id)
    embeds_used = usage_repository.get_guild_embeds_created(guild_id, period_key)

    edits_used = None
    if message_id is not None:
        edits_used = usage_repository.get_embed_edits_used(guild_id, message_id)

    return PlanStatus(
        is_pro=pro,
        period_key=period_key,
        embeds_used=embeds_used,
        embed_limit=None if pro else FREE_EMBED_LIMIT,
        edits_used=edits_used,
        edit_limit=None if pro else FREE_EDIT_LIMIT,
    )


async def ensure_send_allowed(client: discord.Client, guild_id: int) -> str:
    if await is_pro_guild(client, guild_id):
        return usage_repository.ensure_period_rollover(guild_id)

    period_key = usage_repository.ensure_period_rollover(guild_id)
    used = usage_repository.get_guild_embeds_created(guild_id, period_key)
    if used >= FREE_EMBED_LIMIT:
        raise PlanLimitError("Free limit reached (5 embeds this month). Upgrade to Pro for unlimited embeds.")
    return period_key


async def record_send_success(guild_id: int, channel_id: int, message_id: int, period_key: str) -> None:
    usage_repository.increment_guild_embeds_created(guild_id, period_key)
    usage_repository.ensure_embed_record(guild_id, channel_id, message_id)


async def ensure_edit_allowed(client: discord.Client, guild_id: int, message_id: int) -> None:
    if await is_pro_guild(client, guild_id):
        return

    edits_used = usage_repository.get_embed_edits_used(guild_id, message_id)
    if edits_used >= FREE_EDIT_LIMIT:
        raise PlanLimitError("Free edit limit reached (1 edit per embed). Upgrade to Pro for unlimited edits.")


async def record_edit_success(guild_id: int, channel_id: int, message_id: int) -> None:
    usage_repository.increment_embed_edits_used(guild_id, channel_id, message_id)


async def ensure_templates_enabled(client: discord.Client, guild_id: int) -> None:
    if await is_pro_guild(client, guild_id):
        return
    raise FeatureUnavailableError("Templates are a Pro feature. Upgrade to Pro to save, load, and manage templates.")


async def ensure_custom_identity_enabled(client: discord.Client, guild_id: int) -> None:
    if await is_pro_guild(client, guild_id):
        return
    raise FeatureUnavailableError("Custom Identity is a Pro feature. Upgrade to Pro to use custom bot name and avatar.")


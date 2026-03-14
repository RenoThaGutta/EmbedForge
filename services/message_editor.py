from __future__ import annotations

import discord

from config import MANAGED_WEBHOOK_NAME, get_default_pro_avatar_url, get_default_pro_display_name
from domain.embed_draft import EmbedDraft
from errors.app_errors import UnsafeEditTargetError
from repositories.identities import load_guild_identity
from services.entitlements import is_pro_guild
from services.mention_policy import build_allowed_mentions
from services.plans import (
    ensure_edit_allowed,
    ensure_send_allowed,
    record_edit_success,
    record_send_success,
)
from utils.logging import get_logger

logger = get_logger("services.message_editor")


async def _resolve_effective_identity(interaction: discord.Interaction, guild_id: int) -> dict | None:
    if not await is_pro_guild(interaction.client, guild_id):
        return None

    saved_identity = load_guild_identity(guild_id)
    if saved_identity and (saved_identity.get("display_name") or saved_identity.get("avatar_url")):
        return {
            "display_name": str(saved_identity.get("display_name") or "").strip(),
            "avatar_url": str(saved_identity.get("avatar_url") or "").strip(),
        }

    return {
        "display_name": get_default_pro_display_name(),
        "avatar_url": get_default_pro_avatar_url(),
    }


async def _get_managed_webhook(channel: discord.abc.GuildChannel | discord.Thread, bot_user: discord.ClientUser) -> discord.Webhook:
    webhook_channel = channel.parent if isinstance(channel, discord.Thread) else channel
    if not isinstance(webhook_channel, discord.TextChannel):
        raise ValueError("Custom bot identity is not supported in this channel type.")

    webhooks = await webhook_channel.webhooks()
    for webhook in webhooks:
        if webhook.name == MANAGED_WEBHOOK_NAME and webhook.user and webhook.user.id == bot_user.id:
            return webhook

    return await webhook_channel.create_webhook(name=MANAGED_WEBHOOK_NAME)


async def update_draft_message(interaction: discord.Interaction, draft: EmbedDraft) -> None:
    if not draft.edit_channel_id or not draft.edit_message_id:
        raise UnsafeEditTargetError("No edit target set for this builder.")
    if interaction.guild is None:
        raise UnsafeEditTargetError("This action can only be used in a server.")

    await ensure_edit_allowed(interaction.client, interaction.guild.id, draft.edit_message_id)

    channel = interaction.guild.get_channel(draft.edit_channel_id) if interaction.guild else None
    if channel is None:
        channel = await interaction.client.fetch_channel(draft.edit_channel_id)

    if not isinstance(
        channel,
        (discord.TextChannel, discord.Thread, discord.ForumChannel, discord.VoiceChannel, discord.StageChannel),
    ):
        pass

    message = await channel.fetch_message(draft.edit_message_id)
    bot_user = interaction.client.user
    if bot_user is None:
        raise UnsafeEditTargetError("Bot user is not ready.")

    # Check if the message was sent by the bot directly OR via a managed webhook
    is_bot_message = message.author.id == bot_user.id
    managed_webhook: discord.Webhook | None = None
    if not is_bot_message and message.webhook_id is not None:
        try:
            managed_webhook = await _get_managed_webhook(channel, bot_user)
            is_bot_message = message.webhook_id == managed_webhook.id
        except (ValueError, discord.HTTPException):
            pass

    if not is_bot_message:
        logger.warning(
            "Rejected unsafe edit target: guild_id=%s channel_id=%s message_id=%s actor_id=%s author_id=%s",
            getattr(interaction.guild, "id", None),
            draft.edit_channel_id,
            draft.edit_message_id,
            getattr(interaction.user, "id", None),
            getattr(message.author, "id", None),
        )
        raise UnsafeEditTargetError("You can only update messages sent by this bot.")

    embed = draft.build_embed()
    view = draft.build_view()
    allowed_mentions = build_allowed_mentions(draft)

    content: str | None
    if embed is not None:
        content = str(draft.mention_text or "").strip() or None
    else:
        content = str(draft.message or "").strip()
        if draft.mention_text:
            content = (content + ("\n" if content else "") + str(draft.mention_text).strip()).strip()
        content = content or None

    # Use webhook.edit_message for webhook-sent messages, otherwise use message.edit
    if managed_webhook is not None:
        kwargs: dict = {"allowed_mentions": allowed_mentions}
        if content is not None:
            kwargs["content"] = content
        else:
            kwargs["content"] = ""
        if embed is not None:
            kwargs["embed"] = embed
        else:
            kwargs["embeds"] = []
        if view is not None:
            kwargs["view"] = view
        await managed_webhook.edit_message(message.id, **kwargs)
    else:
        await message.edit(
            content=content,
            embed=embed if embed is not None else None,
            view=view,
            allowed_mentions=allowed_mentions,
        )

    await record_edit_success(interaction.guild.id, draft.edit_channel_id, draft.edit_message_id)


async def send_draft_message(interaction: discord.Interaction, draft: EmbedDraft) -> None:
    channel = interaction.channel
    if channel is None:
        raise ValueError("No channel context.")
    guild = interaction.guild
    if guild is None:
        raise ValueError("This action can only be used in a server.")

    embed = draft.build_embed()
    view = draft.build_view()
    content = None if embed else (draft.message or "")
    if draft.mention_text:
        content = (content or "") + ("\n" if content else "") + draft.mention_text

    allowed_mentions = build_allowed_mentions(draft)
    period_key = await ensure_send_allowed(interaction.client, guild.id)

    identity = await _resolve_effective_identity(interaction, guild.id)

    if identity and (identity.get("display_name") or identity.get("avatar_url")):
        bot_user = interaction.client.user
        if bot_user is None:
            raise ValueError("Bot user is not ready.")
        webhook = await _get_managed_webhook(channel, bot_user)

        kwargs = {"wait": True, "allowed_mentions": allowed_mentions}
        if content:
            kwargs["content"] = content
        if embed is not None:
            kwargs["embed"] = embed
        if view is not None:
            kwargs["view"] = view

        display_name = str(identity.get("display_name") or "").strip()
        avatar_url = str(identity.get("avatar_url") or "").strip()
        if display_name:
            kwargs["username"] = display_name
        if avatar_url:
            kwargs["avatar_url"] = avatar_url
        if isinstance(channel, discord.Thread):
            kwargs["thread"] = channel

        sent_message = await webhook.send(**kwargs)
        await record_send_success(guild.id, getattr(sent_message.channel, "id", channel.id), sent_message.id, period_key)
        return

    if isinstance(channel, discord.ForumChannel):
        kwargs = {"name": draft.title or "Announcement"}
        if content:
            kwargs["content"] = content
        else:
            kwargs["content"] = discord.utils.MISSING
        if embed is not None:
            kwargs["embed"] = embed
        if view is not None:
            kwargs["view"] = view
        kwargs["allowed_mentions"] = allowed_mentions
        created = await channel.create_thread(**kwargs)
        await record_send_success(guild.id, created.thread.id, created.message.id, period_key)
        return

    kwargs = {}
    if content:
        kwargs["content"] = content
    if embed is not None:
        kwargs["embed"] = embed
    if view is not None:
        kwargs["view"] = view
    kwargs["allowed_mentions"] = allowed_mentions
    sent_message = await channel.send(**kwargs)
    await record_send_success(guild.id, sent_message.channel.id, sent_message.id, period_key)


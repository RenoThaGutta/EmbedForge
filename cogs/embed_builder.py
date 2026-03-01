from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from config import get_pro_purchase_url
from domain.embed_draft import EmbedDraft
from errors.app_errors import EmbedForgeError
from repositories.identities import delete_guild_identity, load_guild_identity, save_guild_identity
from services.entitlements import is_pro_guild
from services.embed_renderer import build_preview_embed, draft_from_message
from services.permissions import can_manage_embedforge
from services.plans import (
    FREE_EDIT_LIMIT,
    FREE_EMBED_LIMIT,
    ensure_custom_identity_enabled,
    ensure_edit_allowed,
    get_plan_status,
)
from utils.logging import get_logger
from views.embed_builder_view import EmbedMakerView

logger = get_logger("cogs.embed_builder")


async def send_builder_response(interaction: discord.Interaction, draft: EmbedDraft) -> None:
    templates_enabled = bool(interaction.guild and await is_pro_guild(interaction.client, interaction.guild.id))
    view = EmbedMakerView(draft, author_id=interaction.user.id, templates_enabled=templates_enabled)
    draft._view_ref = view

    content = view.build_preview_content()
    preview_embed = build_preview_embed(draft)

    kwargs = {"content": content, "view": view, "ephemeral": True}
    if preview_embed:
        kwargs["embed"] = preview_embed

    await interaction.response.send_message(**kwargs)

    try:
        view.message = await interaction.original_response()
    except Exception:
        logger.warning("Could not store message reference; live updates may not work")


class EmbedMaker(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="embed_maker", description="Open a simple embed builder for this channel.")
    async def embed_maker(self, interaction: discord.Interaction):
        if not await can_manage_embedforge(interaction):
            try:
                await interaction.response.send_message(
                    "You need **Manage Server** permissions to use this.",
                    ephemeral=True,
                    delete_after=5,
                )
            except Exception:
                pass
            return

        try:
            await send_builder_response(interaction, EmbedDraft())
        except Exception:
            logger.exception("Error in embed_maker command")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "âŒ Failed to create embed maker. Please try again.",
                        ephemeral=True,
                        delete_after=5,
                    )
            except Exception as error_send_fail:
                logger.warning("Could not send error message: %s", error_send_fail)

    @app_commands.command(name="embed_identity", description="View or update this server's custom EmbedForge identity.")
    async def embed_identity(
        self,
        interaction: discord.Interaction,
        display_name: str | None = None,
        avatar_url: str | None = None,
        reset: bool = False,
    ):
        if interaction.guild is None:
            return await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)

        if not await can_manage_embedforge(interaction):
            return await interaction.response.send_message(
                "You need **Manage Server** permissions to use this.",
                ephemeral=True,
                delete_after=5,
            )

        guild_id = interaction.guild.id

        if reset:
            deleted = delete_guild_identity(guild_id)
            if deleted:
                await interaction.response.send_message(
                    "âœ… This server's custom bot identity has been reset.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    "This server is currently using the default bot identity.",
                    ephemeral=True,
                )
            return

        current = load_guild_identity(guild_id)

        if display_name is None and avatar_url is None:
            if not await is_pro_guild(interaction.client, guild_id):
                await interaction.response.send_message(
                    "Custom Identity is a Pro feature. Upgrade to Pro to use a custom bot name and avatar.",
                    ephemeral=True,
                )
                return

            if not current:
                await interaction.response.send_message(
                    "This server is currently using the default bot identity.",
                    ephemeral=True,
                )
                return

            avatar_text = current.get("avatar_url") or "Not set"
            await interaction.response.send_message(
                f"**Current server identity**\nName: `{current.get('display_name') or 'Default'}`\nAvatar: {avatar_text}",
                ephemeral=True,
            )
            return

        try:
            await ensure_custom_identity_enabled(interaction.client, guild_id)
        except Exception as exc:
            return await interaction.response.send_message(str(exc), ephemeral=True)

        updated_name = str(display_name if display_name is not None else (current or {}).get("display_name", "")).strip()
        updated_avatar = str(avatar_url if avatar_url is not None else (current or {}).get("avatar_url", "")).strip()

        if not updated_name:
            return await interaction.response.send_message(
                "Provide a display name, or use `reset: true` to clear the custom identity.",
                ephemeral=True,
            )

        if len(updated_name) > 80:
            return await interaction.response.send_message(
                "Display name must be 80 characters or fewer.",
                ephemeral=True,
            )

        if updated_avatar and len(updated_avatar) > 1024:
            return await interaction.response.send_message(
                "Avatar URL must be 1024 characters or fewer.",
                ephemeral=True,
            )

        save_guild_identity(guild_id, updated_name, updated_avatar)
        avatar_text = updated_avatar or "Not set"
        await interaction.response.send_message(
            f"âœ… Saved this server's bot identity.\nName: `{updated_name}`\nAvatar: {avatar_text}",
            ephemeral=True,
        )

    @app_commands.command(name="plan", description="Show this server's EmbedForge plan and current usage.")
    async def plan(self, interaction: discord.Interaction, message_id: str | None = None):
        if interaction.guild is None:
            return await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)

        parsed_message_id: int | None = None
        if message_id is not None:
            try:
                parsed_message_id = int(message_id.strip())
            except ValueError:
                return await interaction.response.send_message("`message_id` must be a numeric Discord message ID.", ephemeral=True)

        status = await get_plan_status(interaction.client, interaction.guild.id, parsed_message_id)

        if status.is_pro:
            lines = [
                "**EmbedForge Plan**",
                "Plan: **Pro**",
                "Embeds: Unlimited",
                "Edits per embed: Unlimited",
                "Templates: Enabled",
                "Custom Identity: Enabled",
                "Pro identity appears on sent messages, not preview or command response messages.",
            ]
        else:
            purchase_url = get_pro_purchase_url()
            lines = [
                "**EmbedForge Plan**",
                "Plan: **Free**",
                f"Embeds used this period ({status.period_key}): **{status.embeds_used}/{FREE_EMBED_LIMIT}**",
                f"Edits per embed: **{FREE_EDIT_LIMIT}**",
                "Templates: Disabled",
                "Custom Identity: Disabled",
                "Upgrade to Pro for unlimited embeds, unlimited edits, templates, and custom identity.",
                f"Upgrade here: {purchase_url}",
            ]
            if parsed_message_id is not None:
                lines.insert(
                    3,
                    f"Edits used for message `{parsed_message_id}`: **{status.edits_used or 0}/{FREE_EDIT_LIMIT}**",
                )

        await interaction.response.send_message("\n".join(lines), ephemeral=True)


@app_commands.context_menu(name="Edit Embed")
async def edit_embed_message_context(interaction: discord.Interaction, message: discord.Message):
    if interaction.guild is None:
        return await interaction.response.send_message("This must be used in a server.", ephemeral=True)

    if not await can_manage_embedforge(interaction):
        return await interaction.response.send_message(
            "You need **Manage Server** permissions to use this.",
            ephemeral=True,
            delete_after=5,
        )

    try:
        await ensure_edit_allowed(interaction.client, interaction.guild.id, message.id)
        await send_builder_response(interaction, draft_from_message(message))
    except EmbedForgeError as exc:
        if not interaction.response.is_done():
            await interaction.response.send_message(f"âŒ {exc}", ephemeral=True, delete_after=8)
    except Exception:
        logger.exception("Error in Edit Embed context menu")
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("âŒ Failed to open editor.", ephemeral=True, delete_after=5)
        except Exception:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(EmbedMaker(bot))

    try:
        bot.tree.remove_command("Edit Embed", type=discord.AppCommandType.message)
    except Exception:
        pass
    bot.tree.add_command(edit_embed_message_context)


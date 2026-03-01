from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from errors.app_errors import EmbedForgeError
from repositories.templates import delete_embed_template, get_template_info, load_embed_template
from services.plans import ensure_templates_enabled
from utils.logging import get_logger

if TYPE_CHECKING:
    from domain.embed_draft import EmbedDraft
    from views.embed_builder_view import EmbedMakerView

logger = get_logger("views.template_views")


class TemplateSelectView(discord.ui.View):
    def __init__(self, draft: "EmbedDraft", main_view: "EmbedMakerView", guild_id: int, templates: list):
        super().__init__(timeout=60)
        self.draft = draft
        self.main_view = main_view
        self.guild_id = guild_id

        options = []
        for template_name in templates[:25]:
            options.append(
                discord.SelectOption(
                    label=template_name,
                    description=f"Load template: {template_name}",
                    value=template_name,
                )
            )

        if options:
            self.template_select.options = options
        else:
            self.template_select.disabled = True
            self.template_select.placeholder = "No templates available"

    @discord.ui.select(placeholder="Choose a template to load...", min_values=1, max_values=1)
    async def template_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        try:
            await ensure_templates_enabled(interaction.client, self.guild_id)
            template_name = select.values[0]
            data = load_embed_template(template_name, self.guild_id)
            if not data:
                await interaction.response.send_message(
                    f"\u274c Template '{template_name}' not found or corrupted.",
                    ephemeral=True,
                    delete_after=5,
                )
                return

            self.draft.mention_text = data.get("mention_text", "")
            self.draft.title = data.get("title", "")
            self.draft.message = data.get("message", "")
            self.draft.image_url = data.get("image_url", "")
            self.draft.btn_label = data.get("btn_label", "")
            self.draft.btn_url = data.get("btn_url", "")
            self.draft.footer_text = data.get("footer_text", "")
            self.draft.footer_icon_url = data.get("footer_icon_url", "")
            self.draft.thumbnail_url = data.get("thumbnail_url", "")
            self.draft.author_name = data.get("author_name", "")
            self.draft.author_icon_url = data.get("author_icon_url", "")
            self.draft.author_url = data.get("author_url", "")
            self.draft.color_hex = data.get("color_hex", "")
            self.draft.add_timestamp = data.get("add_timestamp", False)
            self.draft.fields = data.get("fields", [])
            self.draft.loaded_template_name = template_name

            await interaction.response.send_message(
                f"\u2705 Loaded template '{template_name}'! Use 'Save Template' to update it.",
                ephemeral=True,
                delete_after=3,
            )

            if hasattr(self.draft, "_view_ref") and self.draft._view_ref:
                try:
                    await self.draft._view_ref.update_preview_direct()
                except Exception as update_error:
                    logger.warning("Failed to update preview after loading template: %s", update_error)
        except EmbedForgeError as exc:
            await interaction.response.send_message(f"\u274c {exc}", ephemeral=True, delete_after=5)
        except Exception as exc:
            logger.exception("Error in template_select")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        f"\u274c An error occurred loading the template: {str(exc)}",
                        ephemeral=True,
                        delete_after=5,
                    )
                else:
                    await interaction.followup.send(
                        f"\u274c An error occurred loading the template: {str(exc)}",
                        ephemeral=True,
                    )
            except Exception:
                pass

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_load(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("\u274c Template loading cancelled.", ephemeral=True, delete_after=2)


class TemplateManageView(discord.ui.View):
    def __init__(self, guild_id: int, templates: list):
        super().__init__(timeout=60)
        self.guild_id = guild_id

        options = []
        for template_name in templates[:25]:
            info = get_template_info(template_name, guild_id)
            description = info["content_summary"][:100] if info else "Template info unavailable"
            options.append(discord.SelectOption(label=template_name, description=description, value=template_name))

        if options:
            self.template_select.options = options
        else:
            self.template_select.disabled = True
            self.template_select.placeholder = "No templates available"

    @discord.ui.select(placeholder="Choose a template to manage...", min_values=1, max_values=1)
    async def template_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        try:
            await ensure_templates_enabled(interaction.client, self.guild_id)
        except Exception as exc:
            await interaction.response.send_message(f"\u274c {exc}", ephemeral=True, delete_after=5)
            return

        template_name = select.values[0]
        info = get_template_info(template_name, self.guild_id)
        if not info:
            await interaction.response.send_message(
                f"\u274c Template '{template_name}' not found.",
                ephemeral=True,
                delete_after=5,
            )
            return

        manage_view = TemplateActionView(template_name, self.guild_id)
        content = f"**Template Management: {template_name}**\n"
        content += f"\U0001f4cb **Content:** {info['content_summary']}\n"
        content += "Choose an action:"
        await interaction.response.send_message(content, view=manage_view, ephemeral=True, delete_after=30)


class TemplateActionView(discord.ui.View):
    def __init__(self, template_name: str, guild_id: int):
        super().__init__(timeout=30)
        self.template_name = template_name
        self.guild_id = guild_id

    @discord.ui.button(label="\U0001f5d1\ufe0f Delete", style=discord.ButtonStyle.danger)
    async def delete_template(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await ensure_templates_enabled(interaction.client, self.guild_id)
        except Exception as exc:
            await interaction.response.send_message(f"\u274c {exc}", ephemeral=True, delete_after=5)
            return
        confirm_view = TemplateDeleteConfirmView(self.template_name, self.guild_id)
        await interaction.response.send_message(
            f"\u26a0\ufe0f **Are you sure you want to delete template '{self.template_name}'?**\n"
            "This action cannot be undone!",
            view=confirm_view,
            ephemeral=True,
            delete_after=20,
        )

    @discord.ui.button(label="\U0001f4dd Update", style=discord.ButtonStyle.primary)
    async def update_template(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await ensure_templates_enabled(interaction.client, self.guild_id)
        except Exception as exc:
            await interaction.response.send_message(f"\u274c {exc}", ephemeral=True, delete_after=5)
            return
        await interaction.response.send_message(
            f"\U0001f4a1 **To update template '{self.template_name}':**\n"
            "1. Use `/embed_maker` to create a new embed\n"
            "2. Set up your embed exactly how you want it\n"
            f"3. Click 'Save Template' and use the same name: `{self.template_name}`\n"
            "4. The template will be automatically updated!\n\n"
            "*Tip: The old version will be completely replaced with your new settings.*",
            ephemeral=True,
            delete_after=15,
        )


class TemplateDeleteConfirmView(discord.ui.View):
    def __init__(self, template_name: str, guild_id: int):
        super().__init__(timeout=20)
        self.template_name = template_name
        self.guild_id = guild_id

    @discord.ui.button(label="\u2705 Yes, Delete", style=discord.ButtonStyle.danger)
    async def confirm_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await ensure_templates_enabled(interaction.client, self.guild_id)
        except Exception as exc:
            await interaction.response.send_message(f"\u274c {exc}", ephemeral=True, delete_after=5)
            return
        success = delete_embed_template(self.template_name, self.guild_id)
        if success:
            await interaction.response.send_message(
                f"\u2705 Template '{self.template_name}' has been deleted.",
                ephemeral=True,
                delete_after=5,
            )
        else:
            await interaction.response.send_message(
                f"\u274c Failed to delete template '{self.template_name}'. It may have already been deleted.",
                ephemeral=True,
                delete_after=5,
            )

    @discord.ui.button(label="\u274c Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("\u274c Deletion cancelled.", ephemeral=True, delete_after=3)


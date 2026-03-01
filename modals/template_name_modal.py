from __future__ import annotations

import discord

from domain.embed_draft import EmbedDraft
from repositories.templates import list_embed_templates, save_embed_template
from services.plans import ensure_templates_enabled


class TemplateNameModal(discord.ui.Modal, title="Save Embed as Template"):
    template_name = discord.ui.TextInput(
        label="Template Name",
        style=discord.TextStyle.short,
        required=True,
        max_length=32,
        placeholder="MyTemplate",
    )

    def __init__(self, draft: EmbedDraft, guild_id: int):
        super().__init__()
        self.draft = draft
        self.guild_id = guild_id

        if draft.loaded_template_name:
            self.template_name.default = draft.loaded_template_name
            self.template_name.placeholder = f"Update: {draft.loaded_template_name}"

            self.warning = discord.ui.TextInput(
                label="\u26a0\ufe0f Updating existing template",
                style=discord.TextStyle.short,
                required=False,
                max_length=50,
                default=f"Will overwrite '{draft.loaded_template_name}'",
                placeholder="Existing template will be overwritten",
            )
            self.add_item(self.warning)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await ensure_templates_enabled(interaction.client, self.guild_id)
        except Exception as exc:
            await interaction.response.send_message(f"\u274c {exc}", ephemeral=True, delete_after=5)
            return

        name = str(self.template_name.value).strip()
        if not name:
            await interaction.response.send_message("\u274c Template name cannot be empty.", ephemeral=True, delete_after=3)
            return

        existing_templates = list_embed_templates(self.guild_id)
        is_loaded_template_update = name == self.draft.loaded_template_name and self.draft.loaded_template_name
        is_overwriting_different = name in existing_templates and not is_loaded_template_update

        if is_overwriting_different:
            await interaction.response.send_message(
                f"\u26a0\ufe0f Template '{name}' already exists and will be overwritten.\n"
                "Use 'Save Template' again to confirm, or change the name to create a new template.",
                ephemeral=True,
                delete_after=8,
            )
            return

        save_embed_template(name, self.draft, self.guild_id)

        if is_loaded_template_update:
            await interaction.response.send_message(
                f"\u2705 Updated template '{name}' for this server!",
                ephemeral=True,
                delete_after=3,
            )
        else:
            await interaction.response.send_message(
                f"\u2705 Saved template '{name}' for this server!",
                ephemeral=True,
                delete_after=3,
            )
            self.draft.loaded_template_name = name


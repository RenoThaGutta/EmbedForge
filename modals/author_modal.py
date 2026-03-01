from __future__ import annotations

import discord

from domain.embed_draft import EmbedDraft


class AuthorModal(discord.ui.Modal, title="Set Author"):
    author_name_input = discord.ui.TextInput(
        label="Author Name",
        style=discord.TextStyle.short,
        required=False,
        max_length=256,
        placeholder="Author name...",
    )
    author_icon_input = discord.ui.TextInput(
        label="Author Icon URL (optional)",
        style=discord.TextStyle.short,
        required=False,
        max_length=1024,
        placeholder="https://...",
    )
    author_url_input = discord.ui.TextInput(
        label="Author URL (optional)",
        style=discord.TextStyle.short,
        required=False,
        max_length=1024,
        placeholder="https://...",
    )

    def __init__(self, draft: EmbedDraft):
        super().__init__()
        self.draft = draft
        self.author_name_input.default = draft.author_name
        self.author_icon_input.default = draft.author_icon_url
        self.author_url_input.default = draft.author_url

    async def on_submit(self, interaction: discord.Interaction):
        self.draft.author_name = str(self.author_name_input.value or "").strip()
        self.draft.author_icon_url = str(self.author_icon_input.value or "").strip()
        self.draft.author_url = str(self.author_url_input.value or "").strip()
        await interaction.response.send_message("\u2705 Updated author.", ephemeral=True, delete_after=3)

        if hasattr(self.draft, "_view_ref") and self.draft._view_ref:
            try:
                await self.draft._view_ref.update_preview_direct()
            except Exception:
                pass


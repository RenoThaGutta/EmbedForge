from __future__ import annotations

import discord

from domain.embed_draft import EmbedDraft


class ImageModal(discord.ui.Modal, title="Set Images"):
    image_input = discord.ui.TextInput(
        label="Main Image URL (large image)",
        style=discord.TextStyle.short,
        required=False,
        max_length=1024,
        placeholder="https://...",
    )
    thumbnail_input = discord.ui.TextInput(
        label="Thumbnail URL (small top-right image)",
        style=discord.TextStyle.short,
        required=False,
        max_length=1024,
        placeholder="https://...",
    )

    def __init__(self, draft: EmbedDraft):
        super().__init__()
        self.draft = draft
        self.image_input.default = draft.image_url
        self.thumbnail_input.default = draft.thumbnail_url

    async def on_submit(self, interaction: discord.Interaction):
        self.draft.image_url = str(self.image_input.value or "").strip()
        self.draft.thumbnail_url = str(self.thumbnail_input.value or "").strip()
        await interaction.response.send_message("\u2705 Updated images.", ephemeral=True, delete_after=3)

        if hasattr(self.draft, "_view_ref") and self.draft._view_ref:
            try:
                await self.draft._view_ref.update_preview_direct()
            except Exception:
                pass


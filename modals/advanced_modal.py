from __future__ import annotations

import discord

from domain.embed_draft import EmbedDraft


class AdvancedModal(discord.ui.Modal, title="Color & Style"):
    color_input = discord.ui.TextInput(
        label="Color (hex like #FF0000, optional)",
        style=discord.TextStyle.short,
        required=False,
        max_length=7,
        placeholder="#FF0000",
    )

    def __init__(self, draft: EmbedDraft):
        super().__init__()
        self.draft = draft
        self.color_input.default = draft.color_hex

    async def on_submit(self, interaction: discord.Interaction):
        self.draft.color_hex = str(self.color_input.value or "").strip()
        await interaction.response.send_message("\u2705 Updated color.", ephemeral=True, delete_after=3)

        if hasattr(self.draft, "_view_ref") and self.draft._view_ref:
            try:
                await self.draft._view_ref.update_preview_direct()
            except Exception:
                pass


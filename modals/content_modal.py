from __future__ import annotations

import discord

from domain.embed_draft import EmbedDraft


class ContentModal(discord.ui.Modal, title="Edit Content"):
    title_input = discord.ui.TextInput(
        label="Embed Title (optional)",
        style=discord.TextStyle.short,
        required=False,
        max_length=256,
    )
    message_input = discord.ui.TextInput(
        label="Message (plain or embed text)",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=4000,
    )

    def __init__(self, draft: EmbedDraft):
        super().__init__()
        self.draft = draft
        self.title_input.default = draft.title
        self.message_input.default = draft.message

    async def on_submit(self, interaction: discord.Interaction):
        self.draft.title = str(self.title_input.value or "").strip()
        self.draft.message = str(self.message_input.value or "").strip()
        await interaction.response.send_message("\u2705 Updated content.", ephemeral=True, delete_after=3)

        if hasattr(self.draft, "_view_ref") and self.draft._view_ref:
            try:
                await self.draft._view_ref.update_preview_direct()
            except Exception:
                pass


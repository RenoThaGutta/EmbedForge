from __future__ import annotations

import discord

from domain.embed_draft import EmbedDraft


class FooterModal(discord.ui.Modal, title="Set Footer"):
    footer_text_input = discord.ui.TextInput(
        label="Footer Text",
        style=discord.TextStyle.short,
        required=False,
        max_length=2048,
        placeholder="Footer text...",
    )
    footer_icon_input = discord.ui.TextInput(
        label="Footer Icon URL (optional)",
        style=discord.TextStyle.short,
        required=False,
        max_length=1024,
        placeholder="https://...",
    )

    def __init__(self, draft: EmbedDraft):
        super().__init__()
        self.draft = draft
        self.footer_text_input.default = draft.footer_text
        self.footer_icon_input.default = draft.footer_icon_url

    async def on_submit(self, interaction: discord.Interaction):
        self.draft.footer_text = str(self.footer_text_input.value or "").strip()
        self.draft.footer_icon_url = str(self.footer_icon_input.value or "").strip()
        await interaction.response.send_message("\u2705 Updated footer.", ephemeral=True, delete_after=3)

        if hasattr(self.draft, "_view_ref") and self.draft._view_ref:
            try:
                await self.draft._view_ref.update_preview_direct()
            except Exception:
                pass


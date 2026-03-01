from __future__ import annotations

import discord

from domain.embed_draft import EmbedDraft


class ButtonModal(discord.ui.Modal, title="Add Link Button (optional)"):
    label_input = discord.ui.TextInput(
        label="Button Label",
        style=discord.TextStyle.short,
        required=False,
        max_length=80,
        placeholder="e.g., Sign Up",
    )
    url_input = discord.ui.TextInput(
        label="Button URL",
        style=discord.TextStyle.short,
        required=False,
        max_length=1024,
        placeholder="https://...",
    )

    def __init__(self, draft: EmbedDraft):
        super().__init__()
        self.draft = draft
        self.label_input.default = draft.btn_label
        self.url_input.default = draft.btn_url

    async def on_submit(self, interaction: discord.Interaction):
        self.draft.btn_label = str(self.label_input.value or "").strip()
        self.draft.btn_url = str(self.url_input.value or "").strip()
        await interaction.response.send_message("\u2705 Updated button.", ephemeral=True, delete_after=3)

        if hasattr(self.draft, "_view_ref") and self.draft._view_ref:
            try:
                await self.draft._view_ref.update_preview_direct()
            except Exception:
                pass


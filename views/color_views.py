from __future__ import annotations

import discord

from domain.embed_draft import EmbedDraft
from modals.advanced_modal import AdvancedModal

COLOR_PRESETS: list[tuple[str, str, str]] = [
    ("Red", "#ED4245", "Rich red"),
    ("Orange", "#EF8843", "Warm orange"),
    ("Gold", "#FBB848", "Discord gold"),
    ("Green", "#3BA55D", "Success green"),
    ("Aqua", "#45DDC0", "Bright aqua"),
    ("Blue", "#5865F2", "Blurple blue"),
    ("Purple", "#9B59B6", "Royal purple"),
    ("Pink", "#EB459E", "Vibrant pink"),
    ("White", "#FFFFFF", "Pure white"),
    ("Grey", "#95A5A6", "Neutral grey"),
    ("Black", "#23272A", "Near black"),
]


async def _refresh_preview(draft: EmbedDraft) -> None:
    if hasattr(draft, "_view_ref") and draft._view_ref:
        try:
            await draft._view_ref.update_preview_direct()
        except Exception:
            pass


class ColorPresetSelect(discord.ui.Select):
    def __init__(self, draft: EmbedDraft):
        self.draft = draft
        options = [
            discord.SelectOption(label=name, value=hex_code, description=f"{description} - {hex_code}")
            for name, hex_code, description in COLOR_PRESETS
        ]
        super().__init__(
            placeholder="Choose a color preset",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        self.draft.color_hex = self.values[0]
        await interaction.response.send_message(f"\u2705 Color set to `{self.draft.color_hex}`.", ephemeral=True)
        await _refresh_preview(self.draft)


class ColorPresetView(discord.ui.View):
    def __init__(self, draft: EmbedDraft):
        super().__init__(timeout=180)
        self.draft = draft
        self.add_item(ColorPresetSelect(draft))

    @discord.ui.button(label="Custom Hex", style=discord.ButtonStyle.secondary)
    async def custom_hex(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(AdvancedModal(self.draft))

    @discord.ui.button(label="Clear Color", style=discord.ButtonStyle.danger)
    async def clear_color(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.draft.color_hex = ""
        await interaction.response.send_message("\u2705 Color reset to default gold.", ephemeral=True)
        await _refresh_preview(self.draft)

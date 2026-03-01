from __future__ import annotations

import discord

from domain.embed_draft import EmbedDraft


class FieldsModal(discord.ui.Modal, title="Add/Edit Fields"):
    field1_name = discord.ui.TextInput(
        label="Field 1 Name (optional)",
        style=discord.TextStyle.short,
        required=False,
        max_length=256,
        placeholder="Field name...",
    )
    field1_value = discord.ui.TextInput(
        label="Field 1 Value (optional)",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=1024,
        placeholder="Field value...",
    )
    field2_name = discord.ui.TextInput(
        label="Field 2 Name (optional)",
        style=discord.TextStyle.short,
        required=False,
        max_length=256,
        placeholder="Field name...",
    )
    field2_value = discord.ui.TextInput(
        label="Field 2 Value (optional)",
        style=discord.TextStyle.paragraph,
        required=False,
        max_length=1024,
        placeholder="Field value...",
    )
    inline_setting = discord.ui.TextInput(
        label="Inline (true/false for all fields)",
        style=discord.TextStyle.short,
        required=False,
        max_length=5,
        placeholder="true",
        default="true",
    )

    def __init__(self, draft: EmbedDraft):
        super().__init__()
        self.draft = draft
        if len(draft.fields) > 0:
            self.field1_name.default = draft.fields[0].get("name", "")
            self.field1_value.default = draft.fields[0].get("value", "")
        if len(draft.fields) > 1:
            self.field2_name.default = draft.fields[1].get("name", "")
            self.field2_value.default = draft.fields[1].get("value", "")

    async def on_submit(self, interaction: discord.Interaction):
        inline_str = str(self.inline_setting.value or "true").strip().lower()
        inline = inline_str in ("true", "yes", "1", "on")

        self.draft.fields = []

        field1_name = str(self.field1_name.value or "").strip()
        field1_value = str(self.field1_value.value or "").strip()
        if field1_name and field1_value:
            self.draft.fields.append({"name": field1_name, "value": field1_value, "inline": inline})

        field2_name = str(self.field2_name.value or "").strip()
        field2_value = str(self.field2_value.value or "").strip()
        if field2_name and field2_value:
            self.draft.fields.append({"name": field2_name, "value": field2_value, "inline": inline})

        field_count = len(self.draft.fields)
        await interaction.response.send_message(
            f"\u2705 Updated fields ({field_count} field{'s' if field_count != 1 else ''}).",
            ephemeral=True,
            delete_after=3,
        )

        if hasattr(self.draft, "_view_ref") and self.draft._view_ref:
            try:
                await self.draft._view_ref.update_preview_direct()
            except Exception:
                pass


from __future__ import annotations

import discord

from domain.embed_draft import EmbedDraft


class MentionDropdown(discord.ui.Select):
    def __init__(self, draft: EmbedDraft, guild: discord.Guild):
        self.draft = draft

        options = [
            discord.SelectOption(label="None", value="none", description="Clear mention", emoji="\u274c"),
            discord.SelectOption(label="@here", value="@here", description="Mention online users", emoji="\U0001f7e2"),
            discord.SelectOption(
                label="@everyone",
                value="@everyone",
                description="Mention all users",
                emoji="\U0001f534",
            ),
        ]

        mentionable_roles = [
            role for role in guild.roles if role.name != "@everyone" and not role.managed and not role.is_bot_managed()
        ]
        mentionable_roles.sort(key=lambda role: role.position, reverse=True)

        for role in mentionable_roles[:22]:
            emoji = "\U0001f451" if role.permissions.administrator else "\U0001f3ad"
            options.append(
                discord.SelectOption(
                    label=f"@{role.name}",
                    value=role.mention,
                    description=f"Mention {role.name} role ({len(role.members)} members)",
                    emoji=emoji,
                )
            )

        super().__init__(placeholder="Choose who to mention...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        selected_value = self.values[0]

        if selected_value == "none":
            self.draft.mention_text = ""
            await interaction.response.send_message("\u2705 Mention cleared.", ephemeral=True, delete_after=3)
        elif selected_value in ["@here", "@everyone"]:
            self.draft.mention_text = selected_value
            await interaction.response.send_message(
                f"\u2705 Set mention to {selected_value}",
                ephemeral=True,
                delete_after=3,
            )
        else:
            self.draft.mention_text = selected_value
            try:
                role_id = selected_value.strip("<@&>")
                guild = interaction.guild
                role = guild.get_role(int(role_id)) if guild else None
                role_name = role.name if role else "Role"
                await interaction.response.send_message(
                    f"\u2705 Set mention to @{role_name}",
                    ephemeral=True,
                    delete_after=3,
                )
            except Exception:
                await interaction.response.send_message("\u2705 Set mention to role", ephemeral=True, delete_after=3)

        if hasattr(self.draft, "_view_ref") and self.draft._view_ref:
            try:
                await self.draft._view_ref.update_preview_direct()
            except Exception:
                pass


class MentionView(discord.ui.View):
    def __init__(self, draft: EmbedDraft, guild: discord.Guild):
        super().__init__(timeout=60)
        self.add_item(MentionDropdown(draft, guild))


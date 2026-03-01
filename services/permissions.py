from __future__ import annotations

import discord


async def can_manage_embedforge(interaction: discord.Interaction) -> bool:
    guild = interaction.guild
    user = interaction.user
    if guild is None:
        return False

    interaction_perms = getattr(interaction, "permissions", None)
    if interaction_perms is not None:
        if interaction_perms.administrator or interaction_perms.manage_guild:
            return True

    member = user if isinstance(user, discord.Member) else guild.get_member(user.id)
    if member is None:
        try:
            member = await guild.fetch_member(user.id)
        except Exception:
            member = None
    if member is None:
        return False

    if guild.owner_id == member.id:
        return True

    perms = member.guild_permissions
    return perms.administrator or perms.manage_guild


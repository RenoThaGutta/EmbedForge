from __future__ import annotations

import re

import discord

from domain.embed_draft import EmbedDraft

ROLE_MENTION_RE = re.compile(r"^<@&(\d+)>$")


def build_allowed_mentions(draft: EmbedDraft) -> discord.AllowedMentions:
    mention_text = str(draft.mention_text or "").strip()

    if mention_text == "@everyone":
        return discord.AllowedMentions(everyone=True, users=False, roles=False, replied_user=False)

    if mention_text == "@here":
        return discord.AllowedMentions(everyone=True, users=False, roles=False, replied_user=False)

    role_match = ROLE_MENTION_RE.fullmatch(mention_text)
    if role_match:
        role_id = int(role_match.group(1))
        role = discord.Object(id=role_id)
        return discord.AllowedMentions(everyone=False, users=False, roles=[role], replied_user=False)

    return discord.AllowedMentions.none()


from __future__ import annotations

import datetime
from typing import Optional

import discord

from domain.embed_draft import EmbedDraft


def has_text(value: Optional[str]) -> bool:
    return bool(value and str(value).strip())


def int_to_hex_color(value: Optional[int]) -> str:
    try:
        if value is None:
            return ""
        return f"#{int(value) & 0xFFFFFF:06X}"
    except Exception:
        return ""


def extract_first_link_button(message: discord.Message) -> tuple[str, str]:
    """Best-effort extraction of the first URL button from a message."""
    try:
        for row in getattr(message, "components", []) or []:
            children = getattr(row, "children", None)
            if children is None:
                children = row

            for component in children or []:
                url = getattr(component, "url", None)
                label = getattr(component, "label", None)
                if url:
                    return (str(label or "Link"), str(url))
    except Exception:
        pass
    return ("", "")


def draft_from_message(message: discord.Message) -> EmbedDraft:
    """Build a draft from an existing Discord message."""
    draft = EmbedDraft()
    content = (message.content or "").strip()

    if message.embeds:
        embed = message.embeds[0]

        draft.mention_text = content
        draft.title = str(embed.title or "").strip()
        draft.message = str(embed.description or "").strip()

        try:
            draft.image_url = str(getattr(embed.image, "url", "") or "").strip()
        except Exception:
            draft.image_url = ""
        try:
            draft.thumbnail_url = str(getattr(embed.thumbnail, "url", "") or "").strip()
        except Exception:
            draft.thumbnail_url = ""
        try:
            draft.footer_text = str(getattr(embed.footer, "text", "") or "").strip()
            draft.footer_icon_url = str(getattr(embed.footer, "icon_url", "") or "").strip()
        except Exception:
            draft.footer_text = ""
            draft.footer_icon_url = ""
        try:
            draft.author_name = str(getattr(embed.author, "name", "") or "").strip()
            draft.author_icon_url = str(getattr(embed.author, "icon_url", "") or "").strip()
            draft.author_url = str(getattr(embed.author, "url", "") or "").strip()
        except Exception:
            draft.author_name = ""
            draft.author_icon_url = ""
            draft.author_url = ""
        try:
            draft.color_hex = int_to_hex_color(getattr(embed.color, "value", None))
        except Exception:
            draft.color_hex = ""

        draft.add_timestamp = bool(getattr(embed, "timestamp", None))
        draft.fields = []

        try:
            for field in getattr(embed, "fields", []) or []:
                name = str(getattr(field, "name", "") or "").strip()
                value = str(getattr(field, "value", "") or "").strip()
                inline = bool(getattr(field, "inline", True))
                if name and value:
                    draft.fields.append({"name": name, "value": value, "inline": inline})
        except Exception:
            draft.fields = []

        label, url = extract_first_link_button(message)
        draft.btn_label = label
        draft.btn_url = url
    else:
        draft.message = content

    if message.guild:
        draft.edit_guild_id = int(message.guild.id)
    if message.channel:
        draft.edit_channel_id = int(message.channel.id)
    draft.edit_message_id = int(message.id)

    return draft


def make_embed(draft: EmbedDraft) -> Optional[discord.Embed]:
    has_title = has_text(draft.title)
    has_desc = has_text(draft.message)
    has_img = has_text(draft.image_url)
    has_content = (
        has_title
        or has_desc
        or has_img
        or has_text(draft.thumbnail_url)
        or has_text(draft.footer_text)
        or has_text(draft.author_name)
        or (draft.fields and len(draft.fields) > 0)
    )

    if not has_content:
        return None

    if not (has_title or has_desc):
        if has_img or has_text(draft.thumbnail_url) or has_text(draft.footer_text) or has_text(draft.author_name):
            has_desc = True
            draft.message = "\u200b"

    color = discord.Color.gold()
    if has_text(draft.color_hex):
        try:
            color = discord.Color(int(draft.color_hex.lstrip("#"), 16))
        except ValueError:
            color = discord.Color.gold()

    kwargs = {"color": color}
    if has_title:
        kwargs["title"] = str(draft.title).strip()
    if has_desc:
        kwargs["description"] = str(draft.message).strip()
    if draft.add_timestamp:
        kwargs["timestamp"] = datetime.datetime.now(datetime.timezone.utc)

    embed = discord.Embed(**kwargs)

    if has_img:
        embed.set_image(url=str(draft.image_url).strip())
    if has_text(draft.thumbnail_url):
        embed.set_thumbnail(url=str(draft.thumbnail_url).strip())
    if has_text(draft.footer_text):
        footer_kwargs = {"text": str(draft.footer_text).strip()}
        if has_text(draft.footer_icon_url):
            footer_kwargs["icon_url"] = str(draft.footer_icon_url).strip()
        embed.set_footer(**footer_kwargs)
    if has_text(draft.author_name):
        author_kwargs = {"name": str(draft.author_name).strip()}
        if has_text(draft.author_icon_url):
            author_kwargs["icon_url"] = str(draft.author_icon_url).strip()
        if has_text(draft.author_url):
            author_kwargs["url"] = str(draft.author_url).strip()
        embed.set_author(**author_kwargs)

    if draft.fields:
        for field in draft.fields:
            if field.get("name") and field.get("value"):
                embed.add_field(
                    name=str(field["name"]).strip()[:256],
                    value=str(field["value"]).strip()[:1024],
                    inline=bool(field.get("inline", True)),
                )

    return embed


def build_preview_embed(draft: EmbedDraft) -> Optional[discord.Embed]:
    embed = draft.build_embed()
    if not embed:
        return None

    preview_embed = discord.Embed(title=embed.title, description=embed.description, color=embed.color)
    if embed.image:
        preview_embed.set_image(url=embed.image.url)
    if embed.thumbnail:
        preview_embed.set_thumbnail(url=embed.thumbnail.url)
    if embed.footer:
        footer_kwargs = {"text": embed.footer.text}
        if embed.footer.icon_url:
            footer_kwargs["icon_url"] = embed.footer.icon_url
        preview_embed.set_footer(**footer_kwargs)
    if embed.author:
        author_kwargs = {"name": embed.author.name}
        if embed.author.icon_url:
            author_kwargs["icon_url"] = embed.author.icon_url
        if embed.author.url:
            author_kwargs["url"] = embed.author.url
        preview_embed.set_author(**author_kwargs)
    if embed.timestamp:
        preview_embed.timestamp = embed.timestamp
    elif draft.add_timestamp:
        preview_embed.timestamp = datetime.datetime.now(datetime.timezone.utc)

    if draft.fields:
        preview_embed.clear_fields()
        for field in draft.fields:
            preview_embed.add_field(
                name=field["name"],
                value=field["value"],
                inline=field.get("inline", True),
            )

    return preview_embed


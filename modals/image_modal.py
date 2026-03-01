from __future__ import annotations

from urllib.parse import urlparse

import discord

from domain.embed_draft import EmbedDraft


IMAGE_HOST_SUFFIXES = (
    "discordapp.net",
    "discordapp.com",
    "discord.com",
    "discordcdn.com",
    "imgur.com",
    "i.imgur.com",
    "githubusercontent.com",
)
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp")


def _looks_like_direct_image_url(value: str) -> bool:
    if not value:
        return True

    try:
        parsed = urlparse(value)
    except Exception:
        return False

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False

    netloc = parsed.netloc.lower()
    path = parsed.path.lower()

    if "drive.google.com" in netloc:
        return False

    if any(path.endswith(ext) for ext in IMAGE_EXTENSIONS):
        return True

    if any(netloc.endswith(host) for host in IMAGE_HOST_SUFFIXES):
        return True

    return False


class ImageModal(discord.ui.Modal, title="Set Images"):
    image_input = discord.ui.TextInput(
        label="Main Image URL",
        style=discord.TextStyle.short,
        required=False,
        max_length=1024,
        placeholder="Direct image URL or Discord attachment URL",
    )
    thumbnail_input = discord.ui.TextInput(
        label="Thumbnail URL",
        style=discord.TextStyle.short,
        required=False,
        max_length=1024,
        placeholder="Direct image URL or Discord attachment URL",
    )

    def __init__(self, draft: EmbedDraft):
        super().__init__()
        self.draft = draft
        self.image_input.default = draft.image_url
        self.thumbnail_input.default = draft.thumbnail_url

    async def on_submit(self, interaction: discord.Interaction):
        image_url = str(self.image_input.value or "").strip()
        thumbnail_url = str(self.thumbnail_input.value or "").strip()

        if not _looks_like_direct_image_url(image_url):
            await interaction.response.send_message(
                "\u274c Main image must be a direct image URL or a Discord attachment link.",
                ephemeral=True,
            )
            return

        if not _looks_like_direct_image_url(thumbnail_url):
            await interaction.response.send_message(
                "\u274c Thumbnail must be a direct image URL or a Discord attachment link.",
                ephemeral=True,
            )
            return

        self.draft.image_url = image_url
        self.draft.thumbnail_url = thumbnail_url
        await interaction.response.send_message("\u2705 Updated images.", ephemeral=True, delete_after=3)

        if hasattr(self.draft, "_view_ref") and self.draft._view_ref:
            try:
                await self.draft._view_ref.update_preview_direct()
            except Exception:
                pass


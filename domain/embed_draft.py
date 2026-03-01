from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import discord


@dataclass
class EmbedDraft:
    mention_text: str = ""
    title: str = ""
    message: str = ""
    image_url: str = ""
    btn_label: str = ""
    btn_url: str = ""
    footer_text: str = ""
    footer_icon_url: str = ""
    thumbnail_url: str = ""
    author_name: str = ""
    author_icon_url: str = ""
    author_url: str = ""
    color_hex: str = ""
    add_timestamp: bool = False
    fields: list = None
    loaded_template_name: str = ""
    edit_guild_id: int = 0
    edit_channel_id: int = 0
    edit_message_id: int = 0

    def __post_init__(self) -> None:
        if self.fields is None:
            self.fields = []

    def build_embed(self) -> Optional[discord.Embed]:
        from services.embed_renderer import make_embed

        return make_embed(self)

    def build_view(self) -> Optional[discord.ui.View]:
        if self.btn_label and self.btn_url:
            class LinkOnly(discord.ui.View):
                def __init__(self, label: str, url: str):
                    super().__init__(timeout=None)
                    self.add_item(discord.ui.Button(label=label, url=url))

            return LinkOnly(self.btn_label, self.btn_url)
        return None


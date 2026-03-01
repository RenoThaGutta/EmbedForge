from __future__ import annotations

import logging
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

from config import get_bot_token
from utils.db import init_db

LOGGER = logging.getLogger("embedforge.bot")
EXTENSIONS = ["Embed_maker"]


class EmbedForgeBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.guilds = True
        intents.messages = True
        super().__init__(command_prefix=commands.when_mentioned, intents=intents)

    async def setup_hook(self) -> None:
        init_db()
        for extension in EXTENSIONS:
            await self.load_extension(extension)
            LOGGER.info("Loaded extension %s", extension)
        synced = await self.tree.sync()
        LOGGER.info("Synced %s app command(s)", len(synced))

    async def on_ready(self) -> None:
        LOGGER.info("Logged in as %s (%s)", self.user, getattr(self.user, "id", "unknown"))


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    bot = EmbedForgeBot()
    bot.run(get_bot_token(), log_handler=None)


if __name__ == "__main__":
    main()


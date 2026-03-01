from __future__ import annotations

import os
from pathlib import Path

import discord
from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parent.parent / ".env")


class SKUPrinter(discord.Client):
    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.none())

    async def on_ready(self) -> None:
        print(f"Logged in as {self.user} ({getattr(self.user, 'id', 'unknown')})")
        skus = await self.fetch_skus()
        if not skus:
            print("No SKUs found for this application.")
        for sku in skus:
            print(f"id={sku.id} name={sku.name!r} type={sku.type} flags={sku.flags}")
        await self.close()


def main() -> None:
    token = os.getenv("DISCORD_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Missing DISCORD_BOT_TOKEN in .env")

    client = SKUPrinter()
    client.run(token, log_handler=None)


if __name__ == "__main__":
    main()


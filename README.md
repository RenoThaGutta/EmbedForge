# EmbedForge

EmbedForge is a Discord bot for building, sending, and editing rich embeds inside Discord.

## Features

- Slash command embed builder: `/embed_maker`
- Message context menu: `Edit Embed`
- Templates
- Free vs Pro feature gating
- Per-server Pro identity support for sent messages
- SQLite-backed usage tracking

## Project Structure

```text
EmbedForge/
├── bot.py
├── config.py
├── requirements.txt
├── cogs/
├── domain/
├── errors/
├── modals/
├── repositories/
├── services/
├── utils/
├── views/
├── .gitignore
├── .env.example
└── README.md
```

## Local Setup

1. Create a virtual environment if you want one.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file based on `.env.example`.
4. Start the bot:

```bash
python bot.py
```

## Environment Variables

Required:

```env
DISCORD_BOT_TOKEN=your_bot_token_here
```

Optional:

```env
EMBEDFORGE_PRO_SKU_ID=
EMBEDFORGE_PRO_URL=https://discord.com/discovery/applications/1477438235608219980/store/1477551786675146804
EMBEDFORGE_PRO_DISPLAY_NAME=EmbedForge Pro
EMBEDFORGE_PRO_AVATAR_URL=https://drive.google.com/uc?export=view&id=1N_lKhtG5O4Y0h1z5mLJp5fWjXmRnNrED
PRO_GUILD_ALLOWLIST=
DB_PATH=
ENTITLEMENT_CACHE_SECONDS=10
```

## Render Deployment

Use these settings for a Background Worker:

- Build Command: `pip install -r requirements.txt`
- Start Command: `python bot.py`

## Notes

- `sqlite3` is part of Python and does not belong in `requirements.txt`.
- Pro identity applies to sent messages, not preview or command response messages.
- If the Pro avatar does not render reliably, replace the default Google Drive URL with a direct image URL in `.env`.

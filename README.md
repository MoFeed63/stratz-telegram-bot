# STRATZ Dota 2 Telegram Bot

A Telegram bot that shows Dota 2 statistics for any player. It talks to the [STRATZ](https://stratz.com) GraphQL API, so the data is the same one you see on the website, only without opening a browser.

Built with aiogram 3 and asyncio: the bot handles several users at the same time and responds fast even during a match.

## Features

- Search a player by Steam profile link, SteamID64 or nickname
- Save up to 3 accounts per user and switch between them with buttons
- Last matches with result, hero, KDA and duration
- Current rank and MMR
- Overall winrate
- Top 5 most played heroes recently
- Partial support for private accounts (shows what the API still returns)
- Handles API timeouts, network errors and Telegram flood limits instead of crashing

## How it works

1. `/start` — the bot creates a keyboard with three account slots.
2. `/add 1` (or 2, 3) — send a Steam link or nickname, then a label for the button.
3. Press an account button — the bot loads the profile and shows a menu: matches, rank, winrate, heroes.
4. Each menu item is an inline button, so switching between views does not restart the dialog.

Accounts are stored in SQLite per Telegram user id, so they survive bot restarts.

## Commands

| Command | Description |
| --- | --- |
| `/start` | Show the account keyboard |
| `/add 1` \| `/add 2` \| `/add 3` | Bind a Steam account to a slot |

The rest of the navigation is buttons only.

## Tech stack

- Python 3.11+
- aiogram 3.x (asyncio)
- httpx — async HTTP client for the STRATZ API
- GraphQL — single query returns profile, matches and hero stats
- aiosqlite — local storage for user accounts
- BeautifulSoup4 / ElementTree — resolving Steam nicknames through profile XML
- python-dotenv — configuration

## Project structure

```
main.py           entry point: handlers, keyboards, FSM states, polling
parser.py         GraphQL query and STRATZ API client
parser_server.py  server-side variant of parser.py, for blocked IPs
steam_id.py       converts Steam links and nicknames to steamID64
formatters.py     builds HTML messages for Telegram from API data
database.py       SQLite layer: user slots, read and update
constants.py      static data: hero ids, rank names
```

## Setup

1. Clone the repo:

```bash
git clone https://github.com/MoFeed63/stratz-telegram-bot
cd stratz-telegram-bot
```

2. Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root:

```env
BOT_TOKEN=your_telegram_bot_token
API_TOKEN=your_stratz_api_token
PROXY_URL=your_proxy_url
```

- `BOT_TOKEN` — from [@BotFather](https://t.me/BotFather)
- `API_TOKEN` — from your STRATZ account, `https://stratz.com/api`
- `PROXY_URL` — optional, needed if Telegram or STRATZ is not reachable from your server

5. Start the bot:

```bash
python main.py
```

`database.db` is created automatically on the first run.

## Notes

- If STRATZ blocks your IP (Cloudflare), use `parser_server.py` or set `PROXY_URL`.
- To reset all saved accounts, just delete `database.db`.
- Logging is set to `DEBUG` in `main.py`; switch to `INFO` for long-running deployments.

## License

Not specified yet.

"""One-time setup for gateway_watch alerts. Run on the VPS: ssh -t root@76.13.179.32 python3 /opt/voyager/deploy/setup_alert.py

Asks for the BotFather token (hidden), finds your chat id from the first message you sent the bot,
saves both to /opt/voyager/alert.env (chmod 600) and sends a test message. The token never leaves the VPS.
"""
import getpass
import json
import os
import re
import urllib.parse
import urllib.request

OUT = "/opt/voyager/alert.env"


def api(token: str, method: str, **params) -> dict:
    data = urllib.parse.urlencode(params).encode() if params else None
    return json.load(urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{token}/{method}", data=data), timeout=15))


raw = getpass.getpass("Bot token from BotFather (hidden): ")
found = re.search(r"\d{6,}:[A-Za-z0-9_-]{30,}", raw)  # tolerates paste junk (bracketed-paste codes, spaces, extra words)
if not found:
    raise SystemExit(f"no bot token found in what was pasted ({len(raw)} characters received; a token is about 46). Nothing changed.")
token = found.group(0)
try:
    me = api(token, "getMe")["result"]
    chats = {u["message"]["chat"]["id"] for u in api(token, "getUpdates")["result"] if "message" in u}
except Exception as exc:  # noqa: BLE001 -- never print exc: its text can contain the token URL
    raise SystemExit(f"Telegram rejected the token or is unreachable ({type(exc).__name__}). Nothing changed.")
if len(chats) != 1:
    raise SystemExit(f"found {len(chats)} chats for @{me['username']}; send ONE message to your bot from your own Telegram, then run again")
chat = chats.pop()
fd = os.open(OUT, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
with os.fdopen(fd, "w") as f:
    f.write(f"TELEGRAM_BOT_TOKEN={token}\nTELEGRAM_CHAT_ID={chat}\n")
api(token, "sendMessage", chat_id=chat, text="Voyager alerts connected. You will only hear from me if the Gateway goes down or the data gate fails.")
print(f"done: saved {OUT} for @{me['username']}, test message sent")

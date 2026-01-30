import json
import os
import urllib.request


def send_message(chat_id: str, text: str, disable_web_page_preview: bool = True) -> dict:
    """Send a message via Telegram Bot API."""
    bot_token = os.getenv("BOT_TOKEN")
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": disable_web_page_preview,
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

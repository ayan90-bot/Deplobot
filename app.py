import os
from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").rstrip("/")
FILES_DIR = os.getenv("FILES_DIR", "files")

if not TELEGRAM_TOKEN:
    raise SystemExit("Please set TELEGRAM_TOKEN in .env or environment variables")

API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return "Bot is running!", 200

@app.route("/set_webhook", methods=["GET"])
def set_webhook():
    if not WEBHOOK_URL:
        return "WEBHOOK_URL not configured", 400
    webhook_endpoint = f"{WEBHOOK_URL}/webhook/{TELEGRAM_TOKEN}"
    resp = requests.post(f"{API_URL}/setWebhook", json={"url": webhook_endpoint})
    return jsonify(resp.json())

@app.route(f"/webhook/{TELEGRAM_TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json(force=True)
    message = update.get("message") or update.get("edited_message")
    if not message:
        return "ok", 200

    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    if text.startswith("/start"):
        send_message(chat_id, "Hello! Send /getfile <filename> to receive a file.")
        return "ok", 200

    if text.startswith("/getfile"):
        parts = text.split(maxsplit=1)
        filename = "bot.py" if len(parts) == 1 else parts[1].strip()

        if ".." in filename or filename.startswith("/") or "\\" in filename:
            send_message(chat_id, "Invalid filename.")
            return "ok", 200

        file_path = os.path.join(FILES_DIR, filename)
        if not os.path.exists(file_path):
            send_message(chat_id, f"File not found: `{filename}`", parse_mode="Markdown")
            return "ok", 200

        send_document(chat_id, file_path)
        return "ok", 200

    send_message(chat_id, "Unknown command. Try /getfile <filename>.")
    return "ok", 200

def send_message(chat_id, text, parse_mode=None):
    data = {"chat_id": chat_id, "text": text}
    if parse_mode:
        data["parse_mode"] = parse_mode
    requests.post(f"{API_URL}/sendMessage", json=data)

def send_document(chat_id, file_path):
    url = f"{API_URL}/sendDocument"
    with open(file_path, "rb") as f:
        files = {"document": (os.path.basename(file_path), f)}
        data = {"chat_id": str(chat_id)}
        requests.post(url, data=data, files=files)

if __name__ == "__main__":
    if WEBHOOK_URL:
        webhook_endpoint = f"{WEBHOOK_URL}/webhook/{TELEGRAM_TOKEN}"
        try:
            requests.post(f"{API_URL}/setWebhook", json={"url": webhook_endpoint})
            print("Webhook set to:", webhook_endpoint)
        except Exception as e:
            print("Webhook setup failed:", e)

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

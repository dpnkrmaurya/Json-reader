#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import subprocess

# ================= AUTO INSTALL =================
REQUIRED_PACKAGES = ["python-telegram-bot==20.7"]

def ensure_packages():
    for pkg in REQUIRED_PACKAGES:
        name = pkg.split("==")[0].replace("-", "_")
        try:
            __import__(name)
        except ImportError:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", pkg]
            )

ensure_packages()

# ================= TOKEN HANDLING =================
TOKEN_FILE = "bot_token.txt"

def get_bot_token():
    # first run: file nahi hai
    if not os.path.exists(TOKEN_FILE):
        print("🔑 First time setup")
        token = input("👉 Enter your Telegram Bot Token: ").strip()

        if not token:
            print("❌ Token empty, exit")
            sys.exit(1)

        with open(TOKEN_FILE, "w") as f:
            f.write(token)

        print(f"✅ Token saved in {TOKEN_FILE}")
        return token

    # next runs: file se read
    with open(TOKEN_FILE, "r") as f:
        token = f.read().strip()

    if not token:
        print("❌ Token file empty, edit bot_token.txt")
        sys.exit(1)

    return token

BOT_TOKEN = get_bot_token()

# ================= IMPORTS =================
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ================= CONFIG =================
BASE_DIR = "files"
os.makedirs(BASE_DIR, exist_ok=True)

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📄 JSON → Simple TXT Report\n"
        "❌ No numbering\n"
        "📱 Termux compatible"
    )

# ================= SIMPLE REPORT =================
def json_to_simple_report(json_path, txt_path):

    def write_value(value, f, indent=0):
        space = "  " * indent

        if isinstance(value, dict):
            for k, v in value.items():
                if isinstance(v, (dict, list)):
                    f.write(f"{space}{k}:\n")
                    write_value(v, f, indent + 1)
                else:
                    f.write(f"{space}{k}: {v}\n")

        elif isinstance(value, list):
            for item in value:
                if isinstance(item, (dict, list)):
                    write_value(item, f, indent + 1)
                else:
                    f.write(f"{space}- {item}\n")

    with open(json_path, "r", encoding="utf-8", errors="ignore") as jf, \
         open(txt_path, "w", encoding="utf-8") as tf:
        data = json.load(jf)
        write_value(data, tf)

# ================= FILE HANDLER =================
async def handle_json(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document

    if not doc.file_name.lower().endswith(".json"):
        await update.message.reply_text("❌ Sirf .json file bheje")
        return

    uid = doc.file_unique_id
    json_path = f"{BASE_DIR}/{uid}.json"
    txt_path = f"{BASE_DIR}/{uid}.txt"

    await update.message.reply_text("⬇️ Download ho raha hai...")
    tg_file = await doc.get_file()
    await tg_file.download_to_drive(json_path)

    await update.message.reply_text("⚙️ Report ban rahi hai...")

    try:
        json_to_simple_report(json_path, txt_path)
        await update.message.reply_document(open(txt_path, "rb"))
    except Exception as e:
        await update.message.reply_text(f"⚠️ Error: {e}")
    finally:
        for f in (json_path, txt_path):
            if os.path.exists(f):
                os.remove(f)

# ================= MAIN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_json))
    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()

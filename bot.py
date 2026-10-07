"""Amharic text-style Telegram bot.
Local:   set BOT_TOKEN=...   then   python bot.py          (polling)
Server:  set BOT_TOKEN and WEBHOOK_URL=https://your-app.example.com  (webhook mode, wakes on message)
"""
import asyncio
import logging
import os
import random
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, MessageHandler, filters)

from styles import CATEGORIES, STYLES, render

logging.basicConfig(level=logging.INFO)
TOKEN = os.environ["BOT_TOKEN"]
MAX_LEN = 40
BTN = InlineKeyboardButton


def categories_kb(has_photo=False):
    rows = [[BTN(label, callback_data=f"cat:{key}")] for key, label in CATEGORIES]
    rows.append([BTN("🎲 ዘፈቀደ", callback_data="rand")])
    if has_photo:
        rows.append([BTN("🗑 ፎቶውን አስወግድ", callback_data="nophoto")])
    return InlineKeyboardMarkup(rows)


def styles_kb(cat):
    items = [(k, v[0]) for k, v in STYLES.items() if v[1] == cat]
    rows = [[BTN(items[i][1], callback_data=f"st:{items[i][0]}")] + (
        [BTN(items[i + 1][1], callback_data=f"st:{items[i + 1][0]}")] if i + 1 < len(items) else [])
        for i in range(0, len(items), 2)]
    rows.append([BTN("◀️ ወደ ምድቦች", callback_data="back")])
    return InlineKeyboardMarkup(rows)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ሰላም! 👋\nየሚፈልጉትን ቃል ወይም ሐረግ ይጻፉልኝ፣ ከዚያ ዘይቤ ይምረጡ።\n\n"
        "📷 የራስዎን ፎቶ እንደ ጀርባ ለመጠቀም ፎቶ ይላኩ።\n"
        "🔒 ፎቶዎ አይቀመጥም፤ ቦቱ ሲዘጋ ይጠፋል።")


async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    f = await update.message.photo[-1].get_file()
    context.user_data["photo"] = bytes(await f.download_as_bytearray())
    msg = "📷 ፎቶው ተቀምጧል! "
    if context.user_data.get("text"):
        await update.message.reply_text(msg + "ምድብ ይምረጡ 👇", reply_markup=categories_kb(True))
    else:
        await update.message.reply_text(msg + "አሁን ጽሑፍ ይጻፉ።")

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text:
        return
    if len(text) > MAX_LEN:
        await update.message.reply_text(f"ጽሑፉ ከ{MAX_LEN} ልክ ይበልጣል::")
        return
    context.user_data["text"] = text
    await update.message.reply_text("ምቅርን ይመርጡ 🎨", reply_markup=categories_kb("photo" in context.user_data))



async def send_result(q, context, key):
    text = context.user_data.get("text")
    if not text:
        await q.message.reply_text("መጀመሪያ ጽሑፍ ይላኩ።")
        return
    photo = context.user_data.get("photo")
    await q.message.chat.send_action("upload_photo")
    buf = await asyncio.to_thread(render, text, key, photo)     # keep the bot responsive
    data = buf.getvalue()
    cat = STYLES[key][1]
    await q.message.reply_document(data, filename="style.png")
    await q.message.reply_photo(data, caption="ሌላ ዘይቤ ይምረጡ ወይም አዲስ ጽሑፍ ይላኩ 👇", reply_markup=styles_kb(cat))


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    d = q.data
    if d == "nophoto":
        context.user_data.pop("photo", None)
        await q.message.reply_text("ፎቶው ተወግዷል።")
    elif d == "back":
        await q.message.reply_text("ምድብ ይምረጡ 👇", reply_markup=categories_kb("photo" in context.user_data))
    elif d == "rand":
        await send_result(q, context, random.choice(list(STYLES)))
    elif d.startswith("cat:"):
        await q.message.reply_text("ዘይቤ ይምረጡ 👇", reply_markup=styles_kb(d[4:]))
    elif d.startswith("st:") and d[3:] in STYLES:
        await send_result(q, context, d[3:])


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, on_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_handler(CallbackQueryHandler(on_button))
    
    url = os.environ.get("WEBHOOK_URL")
    if url:  # server mode
        app.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", "8080")),
            url_path="",
            webhook_url=f"{url.rstrip('/')}/"
        )
    else:
        # your own computer / phone
        app.run_polling()


if name == "main":
    main()

import logging
from telegram import Update, ForceReply, Voice
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import json
import os
import whisper
import tempfile
import subprocess

TOKEN = os.getenv("TOKEN", "7624473465:AAFQ6BhxcrdYm62y43RYj0KQZQ87KStXSF0")
ALLOWED_CHAT_ID = int(os.getenv("CHAT_ID", "-4644207460"))

# Простейшее хранилище (можно заменить на БД или Google Sheets)
data = {
    "tasks": [],
    "reminders": [],
    "lists": {},
    "budget": []
}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

model = whisper.load_model("base")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        await update.message.reply_text("Извините, этот бот — личный помощник Катерина и предназначен только для Марка.")
        return
    await update.message.reply_text(
        "Привет, я Катерина 🤍
Пиши или говори задачи, напоминания, покупки — я всё запомню."
    )

async def process_text_command(update: Update, text: str):
    text = text.lower()
    if text.startswith("добавь задачу"):
        task = text.replace("добавь задачу", "").strip()
        data["tasks"].append({"task": task, "created": datetime.now().isoformat()})
        await update.message.reply_text(f"Задача добавлена: {task}")

    elif text.startswith("список покупок"):
        items = data["lists"].get("покупки", [])
        response = "\n".join(f"- {item}" for item in items) if items else "Список пуст"
        await update.message.reply_text(f"🛒 Список покупок:
{response}")

    elif text.startswith("добавь в список покупок"):
        item = text.replace("добавь в список покупок", "").strip()
        data["lists"].setdefault("покупки", []).append(item)
        await update.message.reply_text(f"Добавила в список: {item}")

    elif text.startswith("покажи задачи"):
        tasks = data["tasks"]
        response = "\n".join(f"• {t['task']}" for t in tasks) if tasks else "Задач пока нет"
        await update.message.reply_text(f"📋 Твои задачи:
{response}")

    elif text.startswith("запиши расход"):
        parts = text.replace("запиши расход", "").strip().split(" на ")
        if len(parts) == 2:
            amount, category = parts
            try:
                data["budget"].append({"amount": float(amount), "category": category, "date": datetime.now().isoformat()})
                await update.message.reply_text(f"Записала {amount} руб на {category}")
            except ValueError:
                await update.message.reply_text("Не могу понять сумму")
        else:
            await update.message.reply_text("Формат: запиши расход 500 на продукты")

    else:
        await update.message.reply_text("Не уверена, что поняла. Попробуй: 'добавь задачу', 'список покупок', 'запиши расход'…")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        return
    text = update.message.text
    await process_text_command(update, text)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.id != ALLOWED_CHAT_ID:
        return

    file = await context.bot.get_file(update.message.voice.file_id)
    with tempfile.TemporaryDirectory() as tmpdir:
        ogg_path = os.path.join(tmpdir, "audio.ogg")
        wav_path = os.path.join(tmpdir, "audio.wav")

        await file.download_to_drive(ogg_path)
        subprocess.run(["ffmpeg", "-i", ogg_path, wav_path], capture_output=True)

        result = model.transcribe(wav_path, language="ru")
        text = result["text"].strip()

        await update.message.reply_text(f"🎤 Ты сказал: {text}")
        await process_text_command(update, text)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    print("Катерина с поддержкой голосовых запущена")
    app.run_polling()

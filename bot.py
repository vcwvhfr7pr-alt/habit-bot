"""
БОТ ДЛЯ НАПОМИНАНИЙ — ТРЕКЕР ПРИВЫЧЕК
Написан на python-telegram-bot без тяжёлых зависимостей.
"""

import os
import json
import asyncio
import logging
import random
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN", "ТОКЕН_ВАШЕГО_БОТА")

DB_FILE = "reminders.json"

def load():
    if os.path.exists(DB_FILE):
        with open(DB_FILE) as f:
            return json.load(f)
    return {}

def save(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

REMINDER_TEXTS = [
    "🌅 Доброе утро! Не забудь отметить свои привычки сегодня. Маленький шаг каждый день — большой результат через год 💪",
    "⚡️ Привет! Напоминаю заглянуть в трекер привычек. Ты уже столько дней не сдавался — не останавливайся!",
    "🎯 Время для привычек! Даже если день суматошный — одна минута чтобы отметить выполненное всегда найдётся.",
    "🔥 Серия не сломается сама по себе — только если ты позволишь. Держи streak живым!",
    "✨ Напоминание дня: твои привычки ждут тебя. Каждое выполнение — это инвестиция в себя будущего.",
    "🌿 Небольшое напоминание — отметить привычки сегодня. Постоянство важнее интенсивности!",
    "💡 Привет! Ты не забыл про свои привычки? Загляни в трекер — это займёт секунду.",
]

# ==========================================
# КОМАНДЫ
# ==========================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я буду напоминать тебе выполнять привычки.\n\n"
        "Команды:\n"
        "🕐 /remind 09:00 — установить напоминание\n"
        "🔕 /remind_off   — отключить напоминание\n"
        "ℹ️ /status       — узнать текущее время напоминания"
    )

async def cmd_remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = update.message.text.strip().split()

    if len(parts) < 2:
        await update.message.reply_text("Укажи время, например:\n/remind 09:00")
        return

    time_str = parts[1]

    try:
        hour, minute = time_str.split(":")
        hour = int(hour)
        minute = int(minute)
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except ValueError:
        await update.message.reply_text("Неверный формат. Используй ЧЧ:ММ, например:\n/remind 08:30")
        return

    reminders = load()
    reminders[str(update.effective_user.id)] = f"{hour:02d}:{minute:02d}"
    save(reminders)

    await update.message.reply_text(
        f"✅ Готово! Каждый день в {hour:02d}:{minute:02d} я буду напоминать тебе о привычках.\n\n"
        f"Чтобы отключить — напиши /remind_off"
    )

async def cmd_remind_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reminders = load()
    uid = str(update.effective_user.id)

    if uid in reminders:
        del reminders[uid]
        save(reminders)
        await update.message.reply_text("🔕 Напоминания отключены.")
    else:
        await update.message.reply_text("У тебя не было активных напоминаний.")

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reminders = load()
    uid = str(update.effective_user.id)

    if uid in reminders:
        await update.message.reply_text(f"🕐 Напоминание установлено на {reminders[uid]} каждый день.")
    else:
        await update.message.reply_text("Напоминаний нет. Установи через /remind 09:00")

# ==========================================
# ФОНОВАЯ ЗАДАЧА — ПРОВЕРЯЕТ ВРЕМЯ КАЖДЫЕ 30 СЕКУНД
# ==========================================

async def reminder_loop(app):
    last_sent = {}

    while True:
        await asyncio.sleep(30)

        now = datetime.now()
        current_time = f"{now.hour:02d}:{now.minute:02d}"
        current_date = now.strftime("%Y-%m-%d")

        reminders = load()

        for user_id, remind_time in reminders.items():
            if remind_time == current_time:
                sent_key = f"{user_id}_{current_date}_{current_time}"
                if sent_key not in last_sent:
                    try:
                        text = random.choice(REMINDER_TEXTS)
                        await app.bot.send_message(int(user_id), text)
                        last_sent[sent_key] = True
                        logging.info(f"Напоминание отправлено: {user_id}")
                    except Exception as e:
                        logging.error(f"Ошибка отправки {user_id}: {e}")

# ==========================================
# ЗАПУСК
# ==========================================

async def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("remind", cmd_remind))
    app.add_handler(CommandHandler("remind_off", cmd_remind_off))
    app.add_handler(CommandHandler("status", cmd_status))

    # Запускаем фоновую задачу напоминаний
    asyncio.create_task(reminder_loop(app))

    # Запускаем бот
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    # Держим бот живым бесконечно
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

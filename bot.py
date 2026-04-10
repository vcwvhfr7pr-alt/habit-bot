import os
import json
import time
import random
import logging
import threading
from datetime import datetime
import telebot

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN", "ТОКЕН_ВАШЕГО_БОТА")
bot = telebot.TeleBot(BOT_TOKEN)

DB_FILE = "reminders.json"

def load():
    if os.path.exists(DB_FILE):
        with open(DB_FILE) as f:
            return json.load(f)
    return {}

def save(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

TEXTS = [
    "🌅 Доброе утро! Не забудь отметить свои привычки сегодня 💪",
    "⚡️ Привет! Напоминаю заглянуть в трекер привычек. Не останавливайся!",
    "🎯 Время для привычек! Одна минута чтобы отметить выполненное.",
    "🔥 Держи streak живым! Загляни в трекер сегодня.",
    "✨ Твои привычки ждут тебя. Каждый день — инвестиция в себя.",
    "🌿 Постоянство важнее интенсивности! Отметь привычки сегодня.",
    "💡 Не забыл про привычки? Загляни в трекер — это займёт секунду.",
]

@bot.message_handler(commands=["start"])
def cmd_start(message):
    bot.reply_to(message,
        "👋 Привет! Я буду напоминать тебе выполнять привычки.\n\n"
        "Команды:\n"
        "🕐 /remind 09:00 — установить напоминание\n"
        "🔕 /remind_off   — отключить напоминание\n"
        "ℹ️ /status       — узнать текущее время напоминания"
    )

@bot.message_handler(commands=["remind"])
def cmd_remind(message):
    parts = message.text.strip().split()
    if len(parts) < 2:
        bot.reply_to(message, "Укажи время, например:\n/remind 09:00")
        return
    try:
        hour, minute = parts[1].split(":")
        hour, minute = int(hour), int(minute)
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except ValueError:
        bot.reply_to(message, "Неверный формат. Используй ЧЧ:ММ, например:\n/remind 08:30")
        return

    reminders = load()
    reminders[str(message.from_user.id)] = f"{hour:02d}:{minute:02d}"
    save(reminders)
    bot.reply_to(message,
        f"✅ Готово! Каждый день в {hour:02d}:{minute:02d} буду напоминать.\n\n"
        "Чтобы отключить — напиши /remind_off"
    )

@bot.message_handler(commands=["remind_off"])
def cmd_remind_off(message):
    reminders = load()
    uid = str(message.from_user.id)
    if uid in reminders:
        del reminders[uid]
        save(reminders)
        bot.reply_to(message, "🔕 Напоминания отключены.")
    else:
        bot.reply_to(message, "У тебя не было активных напоминаний.")

@bot.message_handler(commands=["status"])
def cmd_status(message):
    reminders = load()
    uid = str(message.from_user.id)
    if uid in reminders:
        bot.reply_to(message, f"🕐 Напоминание на {reminders[uid]} каждый день.")
    else:
        bot.reply_to(message, "Напоминаний нет. Установи через /remind 09:00")

def reminder_loop():
    last_sent = {}
    while True:
        time.sleep(30)
        now = datetime.now()
        current_time = f"{now.hour:02d}:{now.minute:02d}"
        current_date = now.strftime("%Y-%m-%d")
        reminders = load()
        for user_id, remind_time in reminders.items():
            if remind_time == current_time:
                key = f"{user_id}_{current_date}_{current_time}"
                if key not in last_sent:
                    try:
                        bot.send_message(int(user_id), random.choice(TEXTS))
                        last_sent[key] = True
                        logging.info(f"Отправлено: {user_id}")
                    except Exception as e:
                        logging.error(f"Ошибка: {e}")

# Запускаем напоминания в отдельном потоке
threading.Thread(target=reminder_loop, daemon=True).start()

# Запускаем бота
logging.info("Бот запущен")
bot.infinity_polling()

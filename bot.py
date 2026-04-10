"""
БОТ ДЛЯ НАПОМИНАНИЙ — ТРЕКЕР ПРИВЫЧЕК
Отправляет ежедневное текстовое напоминание в выбранное время.
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

logging.basicConfig(level=logging.INFO)

# ==========================================
# НАСТРОЙКИ — впишите свои значения
# ==========================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "ТОКЕН_ВАШЕГО_БОТА")

# ==========================================
# ХРАНИЛИЩЕ: { "123456789": "09:00" }
# ==========================================

DB_FILE = "reminders.json"

def load():
    if os.path.exists(DB_FILE):
        with open(DB_FILE) as f:
            return json.load(f)
    return {}

def save(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

# ==========================================
# БОТ
# ==========================================

bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher()

# Тексты напоминаний — каждый день случайно выбирается один
REMINDER_TEXTS = [
    "🌅 Доброе утро! Не забудь отметить свои привычки сегодня. Маленький шаг каждый день — большой результат через год 💪",
    "⚡️ Привет! Напоминаю заглянуть в трекер привычек. Ты уже столько дней не сдавался — не останавливайся!",
    "🎯 Время для привычек! Даже если день суматошный — одна минута чтобы отметить выполненное всегда найдётся.",
    "🔥 Серия не сломается сама по себе — только если ты позволишь. Загляни в трекер и держи streak живым!",
    "✨ Напоминание дня: твои привычки ждут тебя. Каждое выполнение — это инвестиция в себя будущего.",
    "🌿 Небольшое напоминание — отметить привычки сегодня. Постоянство важнее интенсивности!",
    "💡 Привет! Ты не забыл про свои привычки? Открой трекер и отметь что сделано — это займёт секунду.",
]

import random

# ==========================================
# КОМАНДЫ
# ==========================================

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я буду напоминать тебе выполнять привычки.\n\n"
        "Команды:\n"
        "🕐 /remind 09:00 — установить напоминание на нужное время\n"
        "🔕 /remind_off   — отключить напоминание\n"
        "ℹ️ /status       — узнать текущее время напоминания"
    )

@dp.message(Command("remind"))
async def cmd_remind(message: types.Message):
    """Пользователь пишет: /remind 09:00"""
    parts = message.text.strip().split()

    # Проверяем что формат правильный
    if len(parts) < 2:
        await message.answer("Укажи время, например:\n/remind 09:00")
        return

    time_str = parts[1]

    # Проверяем формат ЧЧ:ММ
    try:
        hour, minute = time_str.split(":")
        hour   = int(hour)
        minute = int(minute)
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except ValueError:
        await message.answer("Неверный формат. Используй ЧЧ:ММ, например:\n/remind 08:30")
        return

    # Сохраняем: ключ = строка user_id, значение = "09:00"
    reminders = load()
    reminders[str(message.from_user.id)] = f"{hour:02d}:{minute:02d}"
    save(reminders)

    await message.answer(
        f"✅ Готово! Каждый день в {hour:02d}:{minute:02d} я буду напоминать тебе о привычках.\n\n"
        f"Чтобы отключить — напиши /remind_off"
    )

@dp.message(Command("remind_off"))
async def cmd_remind_off(message: types.Message):
    reminders = load()
    uid = str(message.from_user.id)

    if uid in reminders:
        del reminders[uid]
        save(reminders)
        await message.answer("🔕 Напоминания отключены.")
    else:
        await message.answer("У тебя не было активных напоминаний.")

@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    reminders = load()
    uid = str(message.from_user.id)

    if uid in reminders:
        await message.answer(f"🕐 Напоминание установлено на {reminders[uid]} каждый день.")
    else:
        await message.answer("Напоминаний нет. Установи через /remind 09:00")

# ==========================================
# ФОНОВАЯ ЗАДАЧА — ПРОВЕРЯЕТ ВРЕМЯ КАЖДУЮ МИНУТУ
# ==========================================

async def reminder_loop():
    """
    Каждую минуту смотрим: чьё время напоминания совпадает с текущим?
    Если совпадает — отправляем сообщение.
    Чтобы не отправлять дважды в одну минуту — запоминаем последнюю отправку.
    """
    last_sent = {}  # { user_id: "2024-01-15 09:00" } — когда последний раз отправили

    while True:
        now = datetime.now()
        current_time = f"{now.hour:02d}:{now.minute:02d}"
        current_date = now.strftime("%Y-%m-%d")

        reminders = load()

        for user_id, remind_time in reminders.items():
            if remind_time == current_time:
                # Ключ = пользователь + дата + время, чтобы не слать дважды
                sent_key = f"{user_id}_{current_date}_{current_time}"

                if sent_key not in last_sent:
                    try:
                        text = random.choice(REMINDER_TEXTS)
                        await bot.send_message(int(user_id), text)
                        last_sent[sent_key] = True
                        logging.info(f"Напоминание отправлено пользователю {user_id}")
                    except Exception as e:
                        logging.error(f"Ошибка отправки {user_id}: {e}")

        # Ждём до следующей минуты (проверяем каждые 30 секунд для точности)
        await asyncio.sleep(30)

# ==========================================
# ЗАПУСК
# ==========================================

async def main():
    # Запускаем фоновую задачу напоминаний параллельно с ботом
    asyncio.create_task(reminder_loop())
    # Запускаем бот (polling = бот сам опрашивает Telegram)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

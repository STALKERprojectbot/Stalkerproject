
from aiogram import Bot, Dispatcher, types, executor
import sqlite3
import logging
import random
from datetime import datetime

API_TOKEN = 'YOUR_TOKEN_HERE'
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Подключение к БД
conn = sqlite3.connect('game.db')
cursor = conn.cursor()

# Создание таблиц
cursor.executescript("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    hp INTEGER DEFAULT 100,
    stamina INTEGER DEFAULT 100,
    hunger INTEGER DEFAULT 0,
    location TEXT DEFAULT 'Начальная зона',
    faction TEXT DEFAULT 'Одиночка',
    profession TEXT DEFAULT 'Новичок',
    skills TEXT DEFAULT '',
    inventory TEXT DEFAULT '',
    artifacts TEXT DEFAULT '',
    shelter_level INTEGER DEFAULT 1,
    is_admin INTEGER DEFAULT 0,
    money INTEGER DEFAULT 100
);

CREATE TABLE IF NOT EXISTS clans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    leader_id INTEGER
);

CREATE TABLE IF NOT EXISTS auctions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id INTEGER,
    item TEXT,
    price INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
""")
conn.commit()

# Команда /start
@dp.message_handler(commands=['start'])
async def start_game(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"
    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()
        await message.answer("Ты зарегистрирован в Зоне.")
    else:
        await message.answer("Ты уже зарегистрирован.")

# Главное меню
@dp.message_handler(commands=['menu'])
async def show_menu(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["🎒 Инвентарь", "⚔️ Бой", "🧪 Артефакты", "🏠 Убежище", "🧬 Навыки", "👥 Клан", "💰 Аукцион"]
    keyboard.add(*buttons)
    await message.answer("Выбери действие:", reply_markup=keyboard)

# Кнопочные действия
@dp.message_handler(lambda message: message.text == "🎒 Инвентарь")
async def inventory(message: types.Message):
    cursor.execute("SELECT inventory FROM users WHERE id=?", (message.from_user.id,))
    inv = cursor.fetchone()[0] or ""
    await message.answer(f"Твой инвентарь: {inv if inv else 'Пусто'}")

@dp.message_handler(lambda message: message.text == "⚔️ Бой")
async def fight(message: types.Message):
    success = random.random() > 0.3
    reward = random.randint(10, 50) if success else 0
    cursor.execute("UPDATE users SET money = money + ? WHERE id=?", (reward, message.from_user.id))
    conn.commit()
    await message.answer("Ты победил врага и получил {} монет!".format(reward) if success else "Ты проиграл бой, но остался жив.")

@dp.message_handler(lambda message: message.text == "🧪 Артефакты")
async def artifacts(message: types.Message):
    cursor.execute("SELECT artifacts FROM users WHERE id=?", (message.from_user.id,))
    data = cursor.fetchone()[0] or ""
    await message.answer(f"Артефакты: {data if data else 'Нет артефактов'}")

@dp.message_handler(lambda message: message.text == "🏠 Убежище")
async def shelter(message: types.Message):
    cursor.execute("SELECT shelter_level FROM users WHERE id=?", (message.from_user.id,))
    level = cursor.fetchone()[0]
    await message.answer(f"Уровень убежища: {level}")

@dp.message_handler(lambda message: message.text == "🧬 Навыки")
async def skills(message: types.Message):
    await message.answer("Навыки: стрельба, медицина, торговля. Прокачка скоро!")

@dp.message_handler(lambda message: message.text == "👥 Клан")
async def clan_menu(message: types.Message):
    await message.answer("Клановая система в разработке. Используй /create_clan <название>.")

@dp.message_handler(commands=["create_clan"])
async def create_clan(message: types.Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.answer("Используй: /create_clan <название>")
    name = args[1]
    cursor.execute("INSERT INTO clans (name, leader_id) VALUES (?, ?)", (name, message.from_user.id))
    conn.commit()
    await message.answer(f"Клан '{name}' успешно создан!")

@dp.message_handler(lambda message: message.text == "💰 Аукцион")
async def auction(message: types.Message):
    cursor.execute("SELECT item, price FROM auctions ORDER BY timestamp DESC LIMIT 5")
    items = cursor.fetchall()
    text = "\n".join([f"{item} — {price} монет" for item, price in items]) or "Аукцион пуст."
    await message.answer(f"Текущие лоты:\n{text}")

@dp.message_handler(commands=["sell"])
async def sell_item(message: types.Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) != 3:
        return await message.answer("Используй: /sell <предмет> <цена>")
    item, price = parts[1], int(parts[2])
    cursor.execute("INSERT INTO auctions (seller_id, item, price) VALUES (?, ?, ?)", (message.from_user.id, item, price))
    conn.commit()
    await message.answer(f"Выставлен лот: {item} за {price} монет.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
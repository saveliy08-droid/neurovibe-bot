import asyncio
import time
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiohttp import web

BOT_TOKEN = "8935945535:AAGNrZhDJl290DgDIfOZVq6lS3KZXrZjfvQ"
ADMIN_ID = 1722349114
GROUP_ID = -5274257178  # Твой точный ID группы!
PRIVAT_LINK = "https://t.me/+v73ppsyz22w1ZGIy"

# Словарь для хранения КД (айди юзера: время последнего сообщения)
user_cooldowns = {}

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class FeedbackState(StatesGroup):
    waiting_for_message = State()

def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💎 Приватный канал")],
            [KeyboardButton(text="💬 Поддержка и предложения")]
        ],
        resize_keyboard=True
    )

@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        f"Добро пожаловать в neurovibeBOT! ⚡️\n\n"
        f"Здесь ты можешь получить доступ к нашему закрытому комьюнити или связаться с администрацией.\n\n"
        f"Что тут можно сделать?\n"
        f"💎 Приватный канал — забрать актуальную ссылку на вход в приватку.\n"
        f"💬 Поддержка и предложения — задать вопрос, сообщить о проблеме или поделиться своей крутой идеей. Пиши, админ читает абсолютно всё!\n\n"
        f"Выбирай нужный раздел в меню ниже 👇",
        reply_markup=get_main_menu()
    )

@dp.message(F.text == "💎 Приватный канал")
async def privat_channel(message: Message):
    inline_kb = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Вступить в канал 🔓", url=PRIVAT_LINK)]]
    )
    await message.answer("Доступ в наш закрытый приватный канал открыт по кнопке ниже:", reply_markup=inline_kb)

@dp.message(F.text == "💬 Поддержка и предложения")
async def start_feedback(message: Message, state: FSMContext):
    user_id = message.from_user.id
    current_time = time.time()

    # Проверка на КД (60 секунд)
    if user_id in user_cooldowns:
        time_passed = current_time - user_cooldowns[user_id]
        if time_passed < 60:
            time_left = int(60 - time_passed)
            await message.answer(f"⚠️ Не спамь! Ты можешь отправить следующее обращение через {time_left} сек.")
            return

    await state.set_state(FeedbackState.waiting_for_message)
    await message.answer(
        "Напиши своё обращение, вопрос или предложение в одном сообщении (можно прикрепить фото), и я сразу передам его создателю канала.\n\n"
        "Для отмены просто напиши слово «отмена».",
        reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="отмена")]], resize_keyboard=True)
    )

@dp.message(FeedbackState.waiting_for_message)
async def forward_to_admin(message: Message, state: FSMContext):
    if message.text and message.text.lower() == "отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=get_main_menu())
        return

    user_info = (
        f"📩 **Новое обращение!**\n"
        f"👤 От: {message.from_user.full_name} (@{message.from_user.username})\n"
        f"🆔 ID: {message.from_user.id}\n"
        f"✍️ Текст: {message.text if message.text else '[Вложение]'}\n"
    )
    
    # Отправка админу в личку
    await bot.send_message(chat_id=ADMIN_ID, text=user_info)
    if not message.text:
        await message.forward(chat_id=ADMIN_ID)
    
    # Дублирование в группу
    try:
        await bot.send_message(chat_id=GROUP_ID, text=user_info)
        if not message.text:
            await message.forward(chat_id=GROUP_ID)
    except Exception as e:
        print(f"Ошибка отправки в группу: {e}")
    
    # Включаем КД для юзера
    user_cooldowns[message.from_user.id] = time.time()
    
    await state.clear()
    await message.answer("Спасибо! Твое сообщение успешно отправлено администратору. Ожидай ответа.", reply_markup=get_main_menu())

@dp.message(F.reply_to_message)
async def reply_to_user(message: Message):
    is_admin_cl = message.chat.id == ADMIN_ID
    is_admin_gr = message.chat.id == GROUP_ID
    
    if not (is_admin_cl or is_admin_gr):
        return

    reply = message.reply_to_message
    if not reply.text:
        return

    try:
        lines = reply.text.split("\n")
        user_id_line = [line for line in lines if "ID:" in line or "🆔 ID:" in line][0]
        user_id = int(''.join(filter(str.isdigit, user_id_line)))
    except Exception:
        await message.answer("❌ Не удалось найти ID пользователя в этом сообщении.")
        return

    try:
        if message.text:
            await bot.send_message(chat_id=user_id, text=f"💬 **Ответ от администрации:**\n\n{message.text}")
        else:
            await bot.send_message(chat_id=user_id, text=f"💬 **Ответ от администрации (вложение):**\n")
            await message.copy_to(chat_id=user_id)
        await message.answer("✅ Ответ успешно доставлен!")
    except Exception as e:
        await message.answer(f"❌ Не удалось отправить. Ошибка: {e}")

async def handle(request):
    return web.Response(text="Бот работает!")

async def start_webserver():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 10000)
    await site.start()

async def main():
    await start_webserver()
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

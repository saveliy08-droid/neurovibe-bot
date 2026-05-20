import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiohttp import web

BOT_TOKEN = "8935945535:AAGNrZhDJl290DgDIfOZVq6lS3KZXrZjfvQ"
ADMIN_ID = 1722349114
PRIVAT_LINK = "https://t.me/+v73ppsyz22w1ZGIy"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class FeedbackState(StatesGroup):
    waiting_for_message = State()

def get_main_menu():
    kb = [
        [KeyboardButton(text="💬 Поддержка и предложения")],
        [KeyboardButton(text="💎 Приватный канал")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        f"Добро пожаловать в **neurovibeBOT**! ⚡️\n\n"
        f"Здесь ты можете получить доступ к нашему закрытому комьюнити или связаться с администрацией.\n\n"
        f"**What тут можно сделать?**\n"
        f"💎 **Приватный канал** — забрать актуальную ссылку на вход в приватку.\n"
        f"💬 **Поддержка и предложения** — задать вопрос или поделиться своей крутой идеей. Админ читает абсолютно всё!\n\n"
        f"Выбери нужный раздел в меню ниже 👇",
        reply_markup=get_main_menu(),
        parse_mode="Markdown"
    )

@dp.message(F.text == "💎 Приватный канал")
async def open_private(message: Message):
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Вступить в приватку 🚀", url=PRIVAT_LINK)]
    ])
    await message.answer(
        "Доступ в наш закрытый приватный канал открыт по кнопке ниже:",
        reply_markup=inline_kb
    )

@dp.message(F.text == "💬 Поддержка и предложения")
async def start_feedback(message: Message, state: FSMContext):
    await state.set_state(FeedbackState.waiting_for_message)
    await message.answer(
        "Напиши своё обращение, вопрос или предложение в одном сообщении "
        "(можно прикрепить фото), и я сразу передам его админу! ✍️\n\n"
        "Для отмены просто напиши слово: отмена"
    )

@dp.message(FeedbackState.waiting_for_message)
async def forward_to_admin(message: Message, state: FSMContext):
    if message.text and message.text.lower() == "отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=get_main_menu())
        return

    user_info = f"👤 От: {message.from_user.full_name} (@{message.from_user.username})\nID: {message.from_user.id}\n\n"
    await bot.send_message(chat_id=ADMIN_ID, text=f"⚠️ Новое обращение!\n\n{user_info}")
    await message.forward(chat_id=ADMIN_ID)
    
    await state.clear()
    await message.answer("Спасибо! Твое сообщение успешно отправлено администратору. Ожидай ответа.", reply_markup=get_main_menu())

# Хак для обхода спящего режима Render (мини веб-сервер)
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
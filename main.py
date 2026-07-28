from steam_id import get_steam_id
import asyncio
from parser import get_player
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import Message, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
import os
from dotenv import load_dotenv
import logging
from constants import STEAM_ID64_BASE
from formatters import format_player

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
PROXY = os.getenv("PROXY_URL")
router = Router()

logging.basicConfig(level=logging.DEBUG)

class Form(StatesGroup):
    wait_steam_id = State()
    choose_topic = State()
    research_steam = State()

def topic_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Последние матчи", callback_data="topic_matches")],
        [InlineKeyboardButton(text="🏆 Ранг", callback_data="topic_rank")],
        [InlineKeyboardButton(text="📈 Винрейт", callback_data="topic_winrate")],
        [InlineKeyboardButton(text="⏳ Недавно сыгранные герои", callback_data="topic_heroes")],
        [InlineKeyboardButton(text="🔍 Найти новый аккаунт", callback_data="topic_research")]
    ])

@router.message(Command("start"))
async def cmd_start(msg: Message, state: FSMContext):
    await state.set_state(Form.wait_steam_id)
    await msg.answer("Привет, скинь ссылку на профиль стим")


@router.message(StateFilter(Form.wait_steam_id))
async def handler(msg: Message, state: FSMContext):
    url = msg.text.strip()
    try:
        steam_id64 = await get_steam_id(url)
        account_id = int(steam_id64) - STEAM_ID64_BASE
    except Exception:
        logging.exception("SteamID error")
        await msg.answer("Не нашёл профиль. Проверь имя и попробуй ещё раз.")
        return
    await state.update_data(account_id=account_id)
    await state.set_state(Form.choose_topic)
    await msg.answer("Нашел профиль, что посмотреть?", reply_markup=topic_button())

@router.callback_query(StateFilter(Form.choose_topic), F.data.startswith("topic_"))
async def on_topic(cb: CallbackQuery, state: FSMContext):
    topic = cb.data.split("_")[1]
    data = await state.get_data()
    account_id = data['account_id']
    player = data.get("player")
    await cb.answer()
    if topic == "research":
        await state.clear()
        await state.set_state(Form.wait_steam_id)
        await cb.message.edit_text("Пришли новый стим аккаунт")
        return
    if not player:
        try:
            player = await get_player(account_id)
            # text = format_player(player, topic)
            await state.update_data(player=player) 
        except Exception:
            logging.exception("Stratz error")
            text = "Ошибка при запросе к Stratz. Повторите попытку или попробуйте позже"
    text = format_player(player, topic)
    if not text:
        text = "❌ Нет данных"
    try:
        await cb.message.edit_text(text, parse_mode="HTML", reply_markup=topic_button())
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


async def main():
    session = AiohttpSession(proxy=PROXY)

    bot = Bot(BOT_TOKEN, session=session)
    dp = Dispatcher()
    dp.include_router(router)
    try:
        await dp.start_polling(bot)
    finally:
        await session.close()


if __name__ == "__main__":
    asyncio.run(main())
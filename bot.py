import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from LANGUAGES import get_text


load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
ADMIN_REPLY_CALLBACK_PREFIX = "admin_reply_to_user_"

bot = Bot(token=TOKEN)
dp = Dispatcher()

class Anonymous(StatesGroup):
    waiting_for_message = State()
    waiting_for_admin_reply = State()
    waiting_for_language = State()
    waiting_for_category = State()

@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang")

    if not lang:
        await state.set_state(Anonymous.waiting_for_language)
        lang_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="O'zbekcha 🇺🇿", callback_data="lang_uz")],
            [InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang_ru")],
            [InlineKeyboardButton(text="English 🇬🇧", callback_data="lang_en")]
        ])
        await message.answer(get_text("language_select_prompt"), reply_markup=lang_keyboard)
        return

    text = (
        get_text("welcome", lang=lang).format(mention=message.from_user.mention_html())
    )
    await message.answer(text, parse_mode="HTML")

@dp.message(Command("lang"))
async def change_language(message: types.Message, state: FSMContext):
    await state.set_state(Anonymous.waiting_for_language)
    lang_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="O'zbekcha 🇺🇿", callback_data="lang_uz")],
        [InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang_ru")],
        [InlineKeyboardButton(text="English 🇬🇧", callback_data="lang_en")]
    ])
    await message.answer(get_text("language_select_prompt"), reply_markup=lang_keyboard)

@dp.callback_query(lambda c: c.data and c.data.startswith("lang_"))
async def language_selection_handler(callback_query: types.CallbackQuery, state: FSMContext):
    lang_code = callback_query.data.split("_")[1]
    # Tilni FSM xotirasida saqlaymiz
    await state.update_data(lang=lang_code)
    
    # Tanlangan til haqida xabar beramiz
    await callback_query.message.delete()
    await callback_query.message.answer(get_text("language_selected", lang=lang_code))
    
    # Holatni (state) tozalash o'rniga, faqat tilni saqlab qolamiz
    await state.set_state(None)
    
    # Asosiy menyuni (welcome message) to'g'ridan-to'g'ri shu yerda ko'rsatamiz
    # start funksiyasini chaqirish o'rniga, matnni shu yerda yuboramiz
    text = get_text("welcome", lang=lang_code).format(mention=callback_query.from_user.mention_html())
    await callback_query.message.answer(text, parse_mode="HTML")

@dp.message(Command("info"))
async def info(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await message.answer(get_text("info_text", lang=lang))

@dp.message(Command("links"))
async def links(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await message.answer(get_text("links_text", lang=lang))

@dp.message(Command("anonim"))
async def anonim_start(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")

    category_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text("category_suggestion", lang=lang), callback_data="category_suggestion")],
        [InlineKeyboardButton(text=get_text("category_complaint", lang=lang), callback_data="category_complaint")],
        [InlineKeyboardButton(text=get_text("category_question", lang=lang), callback_data="category_question")]
    ])
    await message.answer(get_text("anonim_category_prompt", lang=lang), reply_markup=category_keyboard)
    await state.set_state(Anonymous.waiting_for_category)

@dp.callback_query(lambda c: c.data and c.data.startswith("category_"))
async def category_selection_handler(callback_query: types.CallbackQuery, state: FSMContext):
    category = callback_query.data.split("_")[1]
    await state.update_data(category=category)
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await callback_query.message.delete()
    await callback_query.message.answer(get_text("anonim_start_msg", lang=lang))
    await state.set_state(Anonymous.waiting_for_message)
    await callback_query.answer()

@dp.message(Anonymous.waiting_for_message)
async def get_anonim(message: types.Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        user_data = await state.get_data()
        lang = user_data.get("lang", "uz")
        category = user_data.get("category", "Noma'lum")
        caption_text = f"{get_text("new_anonim_request", lang=lang)} ({category})\n🆔 `{user_id}`"
        if message.text:
            reply_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Javob berish", callback_data=f"{ADMIN_REPLY_CALLBACK_PREFIX}{user_id}")]])
            await bot.send_message(ADMIN_ID, f"{caption_text}:\n\n{message.text}", parse_mode="Markdown", reply_markup=reply_markup)
        elif message.photo:
            caption = caption_text
            if message.caption:
                caption += f":\n\n{message.caption}"
            reply_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Javob berish", callback_data=f"{ADMIN_REPLY_CALLBACK_PREFIX}{user_id}")]])
            await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, parse_mode="Markdown", reply_markup=reply_markup)
        elif message.document:
            caption = caption_text
            if message.caption:
                caption += f":\n\n{message.caption}"
            reply_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Javob berish", callback_data=f"{ADMIN_REPLY_CALLBACK_PREFIX}{user_id}")]])
            await bot.send_document(ADMIN_ID, message.document.file_id, caption=caption, parse_mode="Markdown", reply_markup=reply_markup)
        elif message.video:
            caption = caption_text
            if message.caption:
                caption += f":\n\n{message.caption}"
            reply_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Javob berish", callback_data=f"{ADMIN_REPLY_CALLBACK_PREFIX}{user_id}")]])
            await bot.send_video(ADMIN_ID, message.video.file_id, caption=caption, parse_mode="Markdown", reply_markup=reply_markup)
        elif message.voice:
            reply_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Javob berish", callback_data=f"{ADMIN_REPLY_CALLBACK_PREFIX}{user_id}")]])
            await bot.send_voice(ADMIN_ID, message.voice.file_id, caption=caption_text, parse_mode="Markdown", reply_markup=reply_markup)
        elif message.audio:
            reply_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Javob berish", callback_data=f"{ADMIN_REPLY_CALLBACK_PREFIX}{user_id}")]])
            await bot.send_audio(ADMIN_ID, message.audio.file_id, caption=caption_text, parse_mode="Markdown", reply_markup=reply_markup)
        elif message.sticker:
            reply_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Javob berish", callback_data=f"{ADMIN_REPLY_CALLBACK_PREFIX}{user_id}")]])
            await bot.send_sticker(ADMIN_ID, message.sticker.file_id, reply_markup=reply_markup)
            # For stickers, we also send the caption_text separately as stickers don't have captions in the same way as other media
            await bot.send_message(ADMIN_ID, caption_text, parse_mode="Markdown")
        else:
            await message.answer(get_text("content_not_accepted", lang=lang))
            return
        await message.answer(get_text("request_sent", lang=lang))
    except Exception as e:        await message.answer(get_text("error_occurred", lang=lang))
    finally:
        await state.clear()

@dp.callback_query(lambda c: c.data and c.data.startswith(ADMIN_REPLY_CALLBACK_PREFIX))
async def admin_reply_callback_handler(callback_query: CallbackQuery, state: FSMContext):
    user_id = int(callback_query.data.split(ADMIN_REPLY_CALLBACK_PREFIX)[1])
    await state.update_data(reply_to_user_id=user_id)
    await state.set_state(Anonymous.waiting_for_admin_reply)
    user_data = await state.get_data()
    lang = user_data.get("lang", "uz")
    await callback_query.message.answer(get_text("admin_reply_prompt", lang=lang).format(user_id=user_id), parse_mode="Markdown")
    await callback_query.answer()

@dp.message(Anonymous.waiting_for_admin_reply)
async def admin_reply(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        user_id = data.get("reply_to_user_id")

        if not user_id:
            user_data = await state.get_data()
            lang = user_data.get("lang", "uz")
            await message.answer(get_text("user_id_not_found", lang=lang))
            await state.clear()
            return
        user_data = await state.get_data()
        lang = user_data.get("lang", "uz")
        await bot.send_message(user_id, f"{get_text("admin_answer", lang=lang)}:\n\n{message.text}")
        user_data = await state.get_data()
        lang = user_data.get("lang", "uz")
        await message.answer(get_text("admin_reply_sent", lang=lang))
        await state.clear()
    except Exception as e:
        user_data = await state.get_data()
        lang = user_data.get("lang", "uz")
        await message.answer(f"{get_text("error_occurred", lang=lang)}: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

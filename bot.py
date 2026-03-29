import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from LANGUAGES import get_text
from database import (
    init_db, upsert_user,
    save_message, mark_answered, get_last_message_status,
    get_today_count, get_status_counts, get_category_counts,
    get_active_users_count, get_messages_by_category,
)

load_dotenv()

TOKEN    = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
ADMIN_REPLY_PREFIX = "admin_reply_to_user_"
FILTER_PREFIX      = "filter_cat_"

bot = Bot(token=TOKEN)
dp  = Dispatcher()


# ─── States ───────────────────────────────────────────────────────────────────

class Anonymous(StatesGroup):
    waiting_for_message      = State()
    waiting_for_admin_reply  = State()
    waiting_for_language     = State()
    waiting_for_category     = State()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="O'zbekcha 🇺🇿", callback_data="lang_uz")],
        [InlineKeyboardButton(text="Русский 🇷🇺",   callback_data="lang_ru")],
        [InlineKeyboardButton(text="English 🇬🇧",   callback_data="lang_en")],
    ])

def reply_button(user_id: int, message_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="✉️ Javob berish",
            callback_data=f"{ADMIN_REPLY_PREFIX}{user_id}:{message_id}"
        )
    ]])

def stats_filter_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💡 Takliflar",   callback_data=f"{FILTER_PREFIX}suggestion")],
        [InlineKeyboardButton(text="⚠️ Shikoyatlar", callback_data=f"{FILTER_PREFIX}complaint")],
        [InlineKeyboardButton(text="❓ Savollar",    callback_data=f"{FILTER_PREFIX}question")],
    ])

async def get_lang(state: FSMContext) -> str:
    data = await state.get_data()
    return data.get("lang", "uz")

async def clear_state_keep_lang(state: FSMContext):
    """State'ni tozalaydi, lekin tanlangan tilni saqlab qoladi."""
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await state.clear()
    await state.update_data(lang=lang)


# ─── /start ───────────────────────────────────────────────────────────────────

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang")

    if not lang:
        await state.set_state(Anonymous.waiting_for_language)
        await message.answer(get_text("language_select_prompt"), reply_markup=lang_keyboard())
        return

    await upsert_user(message.from_user.id, lang)
    text = get_text("welcome", lang=lang).format(mention=message.from_user.mention_html())
    await message.answer(text, parse_mode="HTML")


# ─── /lang ────────────────────────────────────────────────────────────────────

@dp.message(Command("lang"))
async def cmd_lang(message: Message, state: FSMContext):
    await state.set_state(Anonymous.waiting_for_language)
    await message.answer(get_text("language_select_prompt"), reply_markup=lang_keyboard())


@dp.callback_query(lambda c: c.data and c.data.startswith("lang_"))
async def cb_language(callback: CallbackQuery, state: FSMContext):
    lang_code = callback.data.split("_", 1)[1]
    await state.update_data(lang=lang_code)
    await state.set_state(None)
    await upsert_user(callback.from_user.id, lang_code)

    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(get_text("language_selected", lang=lang_code))
    text = get_text("welcome", lang=lang_code).format(mention=callback.from_user.mention_html())
    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


# ─── /info & /links ───────────────────────────────────────────────────────────

@dp.message(Command("info"))
async def cmd_info(message: Message, state: FSMContext):
    await message.answer(get_text("info_text", lang=await get_lang(state)))

@dp.message(Command("links"))
async def cmd_links(message: Message, state: FSMContext):
    await message.answer(get_text("links_text", lang=await get_lang(state)))


# ─── /status ──────────────────────────────────────────────────────────────────

@dp.message(Command("status"))
async def cmd_status(message: Message, state: FSMContext):
    lang   = await get_lang(state)
    result = await get_last_message_status(message.from_user.id)

    if not result:
        await message.answer(get_text("status_no_messages", lang=lang))
        return

    status_emoji = "✅" if result["status"] == "answered" else "⏳"
    status_label = get_text(f"status_{result['status']}", lang=lang)
    cat_label    = get_text(f"category_{result['category']}", lang=lang)

    text = (
        f"📋 *{get_text('status_title', lang=lang)}*\n\n"
        f"📁 {get_text('status_category', lang=lang)}: {cat_label}\n"
        f"{status_emoji} {get_text('status_label', lang=lang)}: {status_label}\n"
        f"🕐 {get_text('status_sent_at', lang=lang)}: {result['sent_at'][:16]}"
    )
    if result["answered_at"]:
        text += f"\n✉️ {get_text('status_answered_at', lang=lang)}: {result['answered_at'][:16]}"

    await message.answer(text, parse_mode="Markdown")


# ─── /anonim ──────────────────────────────────────────────────────────────────

@dp.message(Command("anonim"))
async def cmd_anonim(message: Message, state: FSMContext):
    lang = await get_lang(state)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text("category_suggestion", lang=lang), callback_data="category_suggestion")],
        [InlineKeyboardButton(text=get_text("category_complaint",  lang=lang), callback_data="category_complaint")],
        [InlineKeyboardButton(text=get_text("category_question",   lang=lang), callback_data="category_question")],
    ])
    await message.answer(get_text("anonim_category_prompt", lang=lang), reply_markup=keyboard)
    await state.set_state(Anonymous.waiting_for_category)


@dp.callback_query(lambda c: c.data and c.data.startswith("category_"))
async def cb_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split("_", 1)[1]
    await state.update_data(category=category)
    lang = await get_lang(state)

    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(get_text("anonim_start_msg", lang=lang))
    await state.set_state(Anonymous.waiting_for_message)
    await callback.answer()


# ─── Receive anonymous message ────────────────────────────────────────────────

@dp.message(Anonymous.waiting_for_message)
async def receive_anonim(message: Message, state: FSMContext):
    data     = await state.get_data()
    lang     = data.get("lang", "uz")
    category = data.get("category", "question")
    user_id  = message.from_user.id

    msg_id = await save_message(user_id, category)
    header = (
        f"{get_text('new_anonim_request', lang=lang)} ({category})\n"
        f"🆔 `{user_id}` | 📨 `#{msg_id}`"
    )
    markup = reply_button(user_id, msg_id)

    try:
        if message.text:
            await bot.send_message(ADMIN_ID, f"{header}:\n\n{message.text}",
                                   parse_mode="Markdown", reply_markup=markup)

        elif message.photo:
            caption = header + (f":\n\n{message.caption}" if message.caption else "")
            await bot.send_photo(ADMIN_ID, message.photo[-1].file_id,
                                 caption=caption, parse_mode="Markdown", reply_markup=markup)

        elif message.document:
            caption = header + (f":\n\n{message.caption}" if message.caption else "")
            await bot.send_document(ADMIN_ID, message.document.file_id,
                                    caption=caption, parse_mode="Markdown", reply_markup=markup)

        elif message.video:
            caption = header + (f":\n\n{message.caption}" if message.caption else "")
            await bot.send_video(ADMIN_ID, message.video.file_id,
                                 caption=caption, parse_mode="Markdown", reply_markup=markup)

        elif message.voice:
            await bot.send_voice(ADMIN_ID, message.voice.file_id,
                                 caption=header, parse_mode="Markdown", reply_markup=markup)

        elif message.audio:
            await bot.send_audio(ADMIN_ID, message.audio.file_id,
                                 caption=header, parse_mode="Markdown", reply_markup=markup)

        elif message.sticker:
            await bot.send_sticker(ADMIN_ID, message.sticker.file_id, reply_markup=markup)
            await bot.send_message(ADMIN_ID, header, parse_mode="Markdown")

        else:
            await message.answer(get_text("content_not_accepted", lang=lang))
            return

        await message.answer(get_text("request_sent", lang=lang))

    except Exception:
        await message.answer(get_text("error_occurred", lang=lang))

    finally:
        await clear_state_keep_lang(state)


# ─── Admin reply flow ─────────────────────────────────────────────────────────

@dp.callback_query(lambda c: c.data and c.data.startswith(ADMIN_REPLY_PREFIX))
async def cb_admin_reply(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Ruxsat yo'q.", show_alert=True)
        return

    parts      = callback.data.split(ADMIN_REPLY_PREFIX, 1)[1].split(":")
    user_id    = int(parts[0])
    message_id = int(parts[1]) if len(parts) > 1 else None

    await state.update_data(reply_to_user_id=user_id, reply_to_message_id=message_id)
    await state.set_state(Anonymous.waiting_for_admin_reply)

    lang = await get_lang(state)
    await callback.message.answer(
        get_text("admin_reply_prompt", lang=lang).format(user_id=user_id),
        parse_mode="Markdown"
    )
    await callback.answer()


@dp.message(Anonymous.waiting_for_admin_reply)
async def send_admin_reply(message: Message, state: FSMContext):
    data       = await state.get_data()
    user_id    = data.get("reply_to_user_id")
    message_id = data.get("reply_to_message_id")
    lang       = data.get("lang", "uz")

    try:
        if not user_id:
            await message.answer(get_text("user_id_not_found", lang=lang))
            return

        await bot.send_message(
            user_id,
            f"{get_text('admin_answer', lang=lang)}:\n\n{message.text}"
        )

        if message_id:
            await mark_answered(message_id)

        await message.answer(get_text("admin_reply_sent", lang=lang))

    except Exception as e:
        await message.answer(f"{get_text('error_occurred', lang=lang)}: {e}")

    finally:
        await clear_state_keep_lang(state)


# ─── /stats (admin only) ──────────────────────────────────────────────────────

@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    today        = await get_today_count()
    statuses     = await get_status_counts()
    categories   = await get_category_counts()
    active_users = await get_active_users_count()

    pending  = statuses.get("pending", 0)
    answered = statuses.get("answered", 0)
    total    = pending + answered

    cat_lines = "\n".join(
        f"  • {k}: {v} ta" for k, v in categories.items()
    ) or "  — ma'lumot yo'q"

    text = (
        f"📊 *Bot statistikasi*\n\n"
        f"👥 Foydalanuvchilar: *{active_users}* ta\n\n"
        f"📨 Bugungi xabarlar: *{today}* ta\n"
        f"📦 Jami xabarlar: *{total}* ta\n\n"
        f"✅ Javob berilgan: *{answered}* ta\n"
        f"⏳ Kutayotganlar: *{pending}* ta\n\n"
        f"📁 Kategoriyalar:\n{cat_lines}"
    )

    await message.answer(text, parse_mode="Markdown", reply_markup=stats_filter_keyboard())


# ─── Category filter ──────────────────────────────────────────────────────────

@dp.callback_query(lambda c: c.data and c.data.startswith(FILTER_PREFIX))
async def cb_filter_category(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Ruxsat yo'q.", show_alert=True)
        return

    category = callback.data.split(FILTER_PREFIX, 1)[1]
    messages = await get_messages_by_category(category)

    if not messages:
        await callback.message.answer(f"📭 *{category}* kategoriyasida xabar yo'q.")
        await callback.answer()
        return

    lines = [f"📁 *{category.upper()}* — so'nggi {len(messages)} ta xabar:\n"]
    for m in messages:
        status_emoji = "✅" if m["status"] == "answered" else "⏳"
        lines.append(
            f"{status_emoji} `#{m['id']}` | 🆔 `{m['user_id']}` | {m['sent_at'][:16]}"
        )

    await callback.message.answer("\n".join(lines), parse_mode="Markdown")
    await callback.answer()


# ─── Entry point ──────────────────────────────────────────────────────────────

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

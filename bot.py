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
    save_message, mark_answered, mark_reviewing, get_message_user_id,
    get_last_message_status,
    get_today_count, get_status_counts, get_category_counts,
    get_active_users_count, get_messages_by_category,
    get_all_user_ids,
    get_all_admin_ids, add_admin, remove_admin,
    save_admin_message, get_admin_messages,
    get_pending_messages,
)

load_dotenv()

# ─── Configuration ────────────────────────────────────────────────────────────

TOKEN         = os.getenv("BOT_TOKEN")
SUPER_ADMIN_ID = int(os.getenv("ADMIN_ID"))  # Bosh admin — faqat Railway Variables dan

ADMIN_REPLY_PREFIX = "admin_reply_to_user_"
FILTER_PREFIX      = "filter_cat_"
BROADCAST_PREFIX   = "broadcast_"
REVIEWING_PREFIX   = "reviewing_msg_"

bot = Bot(token=TOKEN)
dp  = Dispatcher()


# ─── States ───────────────────────────────────────────────────────────────────

class Anonymous(StatesGroup):
    waiting_for_message      = State()
    waiting_for_admin_reply  = State()
    waiting_for_language     = State()
    waiting_for_category     = State()
    waiting_for_broadcast    = State()


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
        ),
        InlineKeyboardButton(
            text="👁 Ko'rib chiqdim",
            callback_data=f"{REVIEWING_PREFIX}{message_id}"
        ),
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
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await state.clear()
    await state.update_data(lang=lang)

async def is_admin(user_id: int) -> bool:
    """Foydalanuvchi admin yoki superadminmi tekshiradi."""
    if user_id == SUPER_ADMIN_ID:
        return True
    admin_ids = await get_all_admin_ids()
    return user_id in admin_ids


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
    status_emoji = {"answered": "✅", "reviewing": "👁", "pending": "⏳"}.get(result["status"], "⏳")
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

    # Barcha adminlarga yuborish
    admin_ids = await get_all_admin_ids()
    all_admins = list({SUPER_ADMIN_ID} | set(admin_ids))

    # content_not_accepted tekshiruvi
    if not (message.text or message.photo or message.document or
            message.video or message.voice or message.audio or message.sticker):
        await message.answer(get_text("content_not_accepted", lang=lang))
        await clear_state_keep_lang(state)
        return

    try:
        for admin_id in all_admins:
            try:
                sent = None
                if message.text:
                    sent = await bot.send_message(admin_id, f"{header}:\n\n{message.text}", parse_mode="Markdown", reply_markup=markup)
                elif message.photo:
                    caption = header + (f":\n\n{message.caption}" if message.caption else "")
                    sent = await bot.send_photo(admin_id, message.photo[-1].file_id, caption=caption, parse_mode="Markdown", reply_markup=markup)
                elif message.document:
                    caption = header + (f":\n\n{message.caption}" if message.caption else "")
                    sent = await bot.send_document(admin_id, message.document.file_id, caption=caption, parse_mode="Markdown", reply_markup=markup)
                elif message.video:
                    caption = header + (f":\n\n{message.caption}" if message.caption else "")
                    sent = await bot.send_video(admin_id, message.video.file_id, caption=caption, parse_mode="Markdown", reply_markup=markup)
                elif message.voice:
                    sent = await bot.send_voice(admin_id, message.voice.file_id, caption=header, parse_mode="Markdown", reply_markup=markup)
                elif message.audio:
                    sent = await bot.send_audio(admin_id, message.audio.file_id, caption=header, parse_mode="Markdown", reply_markup=markup)
                elif message.sticker:
                    sent = await bot.send_sticker(admin_id, message.sticker.file_id, reply_markup=markup)
                    await bot.send_message(admin_id, header, parse_mode="Markdown")

                # Yuborilgan tg_msg_id ni DBga saqlash
                if sent:
                    await save_admin_message(msg_id, admin_id, sent.message_id)

            except Exception:
                pass  # Bitta admin xato bo'lsa, qolganlariga yuborishda davom et

        await message.answer(get_text("request_sent", lang=lang))

    except Exception:
        await message.answer(get_text("error_occurred", lang=lang))
    finally:
        await clear_state_keep_lang(state)


# ─── Admin reply flow ─────────────────────────────────────────────────────────

@dp.callback_query(lambda c: c.data and c.data.startswith(ADMIN_REPLY_PREFIX))
async def cb_admin_reply(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
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
        await bot.send_message(user_id, f"{get_text('admin_answer', lang=lang)}:\n\n{message.text}")
        if message_id:
            await mark_answered(message_id)
            # Barcha adminlardagi tugmalarni o'chirish (javob berildi)
            admin_msgs = await get_admin_messages(message_id)
            for am in admin_msgs:
                try:
                    await bot.edit_message_reply_markup(
                        chat_id=am["admin_id"],
                        message_id=am["tg_msg_id"],
                        reply_markup=None
                    )
                except Exception:
                    pass
        await message.answer(get_text("admin_reply_sent", lang=lang))
    except Exception as e:
        await message.answer(f"{get_text('error_occurred', lang=lang)}: {e}")
    finally:
        await clear_state_keep_lang(state)


# ─── Ko'rib chiqdim ───────────────────────────────────────────────────────────

@dp.callback_query(lambda c: c.data and c.data.startswith(REVIEWING_PREFIX))
async def cb_reviewing(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Ruxsat yo'q.", show_alert=True)
        return
    message_id = int(callback.data.split(REVIEWING_PREFIX, 1)[1])
    await mark_reviewing(message_id)

    # Foydalanuvchiga bildirishnoma
    user_id = await get_message_user_id(message_id)
    if user_id:
        try:
            await bot.send_message(user_id, "👁 Xabaringiz ko'rib chiqilmoqda. Tez orada javob beriladi.")
        except Exception:
            pass

    # Barcha adminlardagi xabar tugmalarini yangilash
    admin_msgs = await get_admin_messages(message_id)
    parts = callback.message.reply_markup.inline_keyboard[0][0].callback_data
    user_id_from_btn = int(parts.split(ADMIN_REPLY_PREFIX, 1)[1].split(":")[0])
    new_markup = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="✉️ Javob berish",
            callback_data=f"{ADMIN_REPLY_PREFIX}{user_id_from_btn}:{message_id}"
        )
    ]])
    for am in admin_msgs:
        try:
            await bot.edit_message_reply_markup(
                chat_id=am["admin_id"],
                message_id=am["tg_msg_id"],
                reply_markup=new_markup
            )
        except Exception:
            pass

    await callback.answer("✅ Foydalanuvchiga bildirishnoma yuborildi.", show_alert=True)


# ─── /stats (admin only) ──────────────────────────────────────────────────────

@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    if not await is_admin(message.from_user.id):
        return
    today        = await get_today_count()
    statuses     = await get_status_counts()
    categories   = await get_category_counts()
    active_users = await get_active_users_count()

    pending   = statuses.get("pending", 0)
    reviewing = statuses.get("reviewing", 0)
    answered  = statuses.get("answered", 0)
    total     = pending + reviewing + answered

    cat_lines = "\n".join(
        f"  • {k}: {v} ta" for k, v in categories.items()
    ) or "  — ma'lumot yo'q"

    text = (
        f"📊 *Bot statistikasi*\n\n"
        f"👥 Foydalanuvchilar: *{active_users}* ta\n\n"
        f"📨 Bugungi xabarlar: *{today}* ta\n"
        f"📦 Jami xabarlar: *{total}* ta\n\n"
        f"✅ Javob berilgan: *{answered}* ta\n"
        f"👁 Ko'rib chiqilmoqda: *{reviewing}* ta\n"
        f"⏳ Kutayotganlar: *{pending}* ta\n\n"
        f"📁 Kategoriyalar:\n{cat_lines}"
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=stats_filter_keyboard())


# ─── Category filter ──────────────────────────────────────────────────────────

@dp.callback_query(lambda c: c.data and c.data.startswith(FILTER_PREFIX))
async def cb_filter_category(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
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
        status_emoji = {"answered": "✅", "reviewing": "👁", "pending": "⏳"}.get(m["status"], "⏳")
        lines.append(f"{status_emoji} `#{m['id']}` | 🆔 `{m['user_id']}` | {m['sent_at'][:16]}")
    await callback.message.answer("\n".join(lines), parse_mode="Markdown")
    await callback.answer()


# ─── /addadmin & /removeadmin (super admin only) ──────────────────────────────

@dp.message(Command("addadmin"))
async def cmd_addadmin(message: Message):
    if message.from_user.id != SUPER_ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("📝 Ishlatish: `/addadmin 123456789`", parse_mode="Markdown")
        return
    new_admin_id = int(parts[1])
    if new_admin_id == SUPER_ADMIN_ID:
        await message.answer("⚠️ Siz allaqachon bosh adminsiz.")
        return
    await add_admin(new_admin_id)
    await message.answer(f"✅ `{new_admin_id}` admin qilib qo'shildi.", parse_mode="Markdown")

@dp.message(Command("removeadmin"))
async def cmd_removeadmin(message: Message):
    if message.from_user.id != SUPER_ADMIN_ID:
        return
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("📝 Ishlatish: `/removeadmin 123456789`", parse_mode="Markdown")
        return
    removed_id = int(parts[1])
    await remove_admin(removed_id)
    await message.answer(f"✅ `{removed_id}` adminlikdan olib tashlandi.", parse_mode="Markdown")

@dp.message(Command("admins"))
async def cmd_admins(message: Message):
    if message.from_user.id != SUPER_ADMIN_ID:
        return
    admin_ids = await get_all_admin_ids()
    if not admin_ids:
        await message.answer(f"👤 Faqat bosh admin: `{SUPER_ADMIN_ID}`", parse_mode="Markdown")
        return
    lines = [f"👑 Bosh admin: `{SUPER_ADMIN_ID}`\n\n👤 Adminlar:"]
    for aid in admin_ids:
        lines.append(f"  • `{aid}`")
    await message.answer("\n".join(lines), parse_mode="Markdown")


# ─── /pending (admin only) ───────────────────────────────────────────────────

@dp.message(Command("pending"))
async def cmd_pending(message: Message):
    if not await is_admin(message.from_user.id):
        return

    msgs = await get_pending_messages()

    if not msgs:
        await message.answer("✅ Javob kutayotgan xabar yo'q!")
        return

    await message.answer(f"⏳ *Javob kutayotgan xabarlar — {len(msgs)} ta*", parse_mode="Markdown")

    for m in msgs:
        status_emoji = "👁" if m["status"] == "reviewing" else "⏳"
        cat_map = {"suggestion": "Taklif", "complaint": "Shikoyat", "question": "Savol"}
        cat = cat_map.get(m["category"], m["category"])
        text = (
            f"{status_emoji} *#{m['id']}* | {cat}\n"
            f"🕐 {m['sent_at'][:16]}"
        )
        markup = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="✉️ Javob berish",
                callback_data=f"{PENDING_PREFIX}{m['user_id']}:{m['id']}"
            )
        ]])
        await message.answer(text, parse_mode="Markdown", reply_markup=markup)


@dp.callback_query(lambda c: c.data and c.data.startswith(PENDING_PREFIX))
async def cb_pending_reply(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("⛔ Ruxsat yo'q.", show_alert=True)
        return

    parts      = callback.data.split(PENDING_PREFIX, 1)[1].split(":")
    user_id    = int(parts[0])
    message_id = int(parts[1])

    await state.update_data(reply_to_user_id=user_id, reply_to_message_id=message_id)
    await state.set_state(Anonymous.waiting_for_admin_reply)

    lang = await get_lang(state)
    await callback.message.answer(
        get_text("admin_reply_prompt", lang=lang).format(user_id=user_id),
        parse_mode="Markdown"
    )
    await callback.answer()


# ─── /broadcast (super admin only) ───────────────────────────────────────────

@dp.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext):
    if message.from_user.id != SUPER_ADMIN_ID:
        return
    user_ids = await get_all_user_ids()
    await state.update_data(broadcast_count=len(user_ids))
    await state.set_state(Anonymous.waiting_for_broadcast)
    await message.answer(
        f"📢 *Broadcast*\n\n"
        f"Yubormoqchi bo'lgan xabaringizni yozing.\n"
        f"👥 Jami *{len(user_ids)}* ta foydalanuvchiga yuboriladi.\n\n"
        f"❌ Bekor qilish uchun /cancel",
        parse_mode="Markdown"
    )

@dp.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    current = await state.get_state()
    if current == Anonymous.waiting_for_broadcast:
        await clear_state_keep_lang(state)
        await message.answer("❌ Broadcast bekor qilindi.")
    else:
        await message.answer("Bekor qilinadigan amal yo'q.")

@dp.message(Anonymous.waiting_for_broadcast)
async def send_broadcast(message: Message, state: FSMContext):
    if message.from_user.id != SUPER_ADMIN_ID:
        return
    user_ids = await get_all_user_ids()
    confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Yuborish",     callback_data=f"{BROADCAST_PREFIX}confirm"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"{BROADCAST_PREFIX}cancel"),
    ]])
    await state.update_data(
        broadcast_text=message.text,
        broadcast_photo=message.photo[-1].file_id if message.photo else None,
        broadcast_video=message.video.file_id if message.video else None,
        broadcast_document=message.document.file_id if message.document else None,
        broadcast_caption=message.caption,
    )
    await message.answer(
        f"📢 *Preview*\nQuyidagi xabar *{len(user_ids)}* ta foydalanuvchiga yuboriladi:",
        parse_mode="Markdown"
    )
    await message.forward(message.from_user.id)
    await message.answer("——————————————", reply_markup=confirm_keyboard)

@dp.callback_query(lambda c: c.data and c.data.startswith(BROADCAST_PREFIX))
async def cb_broadcast(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != SUPER_ADMIN_ID:
        await callback.answer("⛔ Ruxsat yo'q.", show_alert=True)
        return
    action = callback.data.split(BROADCAST_PREFIX, 1)[1]
    if action == "cancel":
        await clear_state_keep_lang(state)
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer("❌ Broadcast bekor qilindi.")
        await callback.answer()
        return

    data     = await state.get_data()
    user_ids = await get_all_user_ids()
    text     = data.get("broadcast_text")
    photo    = data.get("broadcast_photo")
    video    = data.get("broadcast_video")
    document = data.get("broadcast_document")
    caption  = data.get("broadcast_caption")

    try:
        await callback.message.delete()
    except Exception:
        pass

    progress_msg = await callback.message.answer(f"⏳ Yuborilmoqda... 0 / {len(user_ids)}")
    success, failed = 0, 0

    for i, user_id in enumerate(user_ids):
        try:
            if photo:       await bot.send_photo(user_id, photo, caption=caption)
            elif video:     await bot.send_video(user_id, video, caption=caption)
            elif document:  await bot.send_document(user_id, document, caption=caption)
            elif text:      await bot.send_message(user_id, text)
            success += 1
        except Exception:
            failed += 1
        if (i + 1) % 10 == 0:
            try:
                await progress_msg.edit_text(f"⏳ Yuborilmoqda... {i + 1} / {len(user_ids)}")
            except Exception:
                pass
        await asyncio.sleep(0.05)

    await progress_msg.edit_text(
        f"✅ *Broadcast yakunlandi!*\n\n"
        f"👥 Jami: {len(user_ids)} ta\n"
        f"✅ Muvaffaqiyatli: {success} ta\n"
        f"❌ Yuborilmadi: {failed} ta",
        parse_mode="Markdown"
    )
    await clear_state_keep_lang(state)
    await callback.answer()


# ─── Entry point ──────────────────────────────────────────────────────────────

async def main():
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

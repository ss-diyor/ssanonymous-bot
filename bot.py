import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
ADMIN_REPLY_CALLBACK_PREFIX = "admin_reply_to_user_"

bot = Bot(token=TOKEN)
dp = Dispatcher()

class Anonymous(StatesGroup):
    waiting_for_message = State()
    waiting_for_admin_reply = State()

@dp.message(Command("start"))
async def start(message: types.Message):
    text = (
        f"Assalomu alaykum {message.from_user.mention_html()}! \n\n"
        "Bo'stonliq Tumani Ixtisoslashtirilgan Maktabining murojaatlar uchun botiga xush kelibsiz.\n\n"
        "📨 Anonim murojaat: /anonim\n"
        "ℹ️ Maktab haqida: /info\n"
        "🔗 Telegram kanal va Discord server: /links"
    )
    await message.answer(text, parse_mode="HTML")

@dp.message(Command("info"))
async def info(message: types.Message):
    await message.answer(
        "🏫 Bizning maktabimiz 2022-yilda tashkil etilgan bo'lib, asosiy maqsad o'quvchilarga sifatli ta'lim va keng imkoniyatlar yaratishdir. "
        "Maktabimiz zamonaviy o'quv muassasasi bo'lib 5–11-sinflar uchun yuqori sifatli ta'lim beradi. Maktab jamoasi do'stona hamkorlikka tayyor.\n\n"
        "Maktabimizda:\n"
        "- Zamonaviy fanlar darslari (matematika, fizika, ingliz tili, kimyo, biologiya va boshqalar)\n"
        "- Sport va ijodiy to'garaklar.\n"
        "- Tanlov va loyihalarda qatnashish imkoniyati mavjud.\n\n"
        "Siz biz bilan bilim va do'stlikni rivojlantirasiz.\n"
        "Ko'proq yangiliklar uchun Telegram kanalimizga qo'shiling!"
    )

@dp.message(Command("links"))
async def links(message: types.Message):
    await message.answer(
        "📢 Telegram kanal:\n"
        "https://t.me/Bustanlikspecializedschool\n\n"
        "🎮 Discord server (run and managed by senior student):\n"
        "https://discord.gg/RsSFaC8zX"
    )

@dp.message(Command("anonim"))
async def anonim_start(message: types.Message, state: FSMContext):
    await message.answer("✍️ Murojaatingizni yozishingiz mumkin.\n\n📎 Matn, rasm, ovozli xabar yoki fayl yuborishingiz mumkin.")
    await state.set_state(Anonymous.waiting_for_message)

@dp.message(Anonymous.waiting_for_message)
async def get_anonim(message: types.Message, state: FSMContext):
    try:
        user_id = message.from_user.id
        caption_text = f"📩 Yangi anonim murojaat\n🆔 `{user_id}`"
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
            await message.answer("⚠️ Bu turdagi kontent qabul qilinmaydi.")
            return
        await message.answer("✅ Murojaatingiz yuborildi. Rahmat.")
    except Exception as e:
        await message.answer("❌ Xatolik yuz berdi. Qayta urinib ko'ring.")
    finally:
        await state.clear()

@dp.callback_query(lambda c: c.data and c.data.startswith(ADMIN_REPLY_CALLBACK_PREFIX))
async def admin_reply_callback_handler(callback_query: CallbackQuery, state: FSMContext):
    user_id = int(callback_query.data.split(ADMIN_REPLY_CALLBACK_PREFIX)[1])
    await state.update_data(reply_to_user_id=user_id)
    await state.set_state(Anonymous.waiting_for_admin_reply)
    await callback_query.message.answer(f"Foydalanuvchi ID: `{user_id}` ga javob yozishingiz mumkin.", parse_mode="Markdown")
    await callback_query.answer()

@dp.message(Anonymous.waiting_for_admin_reply)
async def admin_reply(message: types.Message):
    try:
        data = await state.get_data()
        user_id = data.get("reply_to_user_id")

        if not user_id:
            await message.answer("❌ Foydalanuvchi ID topilmadi. Iltimos, 'Javob berish' tugmasi orqali javob bering.")
            await state.clear()
            return
        await bot.send_message(user_id, f"📬 Admin javobi:\n\n{message.text}")
        await message.answer("✅ Javob yuborildi.")
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

load_dotenv()

TOKEN = os.getenv("8409695955:AAG085BWrkAhonfBxDFFD4d1vJJx_JJJAss")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher()

class Anonymous(StatesGroup):
    waiting_for_message = State()

@dp.message(Command("start"))
async def start(message: types.Message):
    text = (
        f"Assalomu alaykum {message.from_user.mention_html()}! \n\n"
        "Bo'stonliq tuman ixtisoslashtirilgan maktabining murojaatlar uchun botiga xush kelibsiz.\n\n"
        "📨 Anonim murojaat: /anonim\n"
        "ℹ️ Maktab haqida: /info\n"
        "🔗 Telegram kanal va Discord server: /links"
    )
    await message.answer(text, parse_mode="HTML")

@dp.message(Command("info"))
async def info(message: types.Message):
    await message.answer(
        "🏫 Bizning maktabimiz 2022-yilda tashkil etilgan bo'lib, asosiy maqsad o'quvchilarga sifatli ta'lim va keng imkoniyatlar yaratishdir. "
        "Maktabimiz zamonaviy o'quv muassasasi bo'lib 5–11-sinflar uchun yuqori darajadagi ta'lim beriladi. Maktab jamoasi do'stona hamkorlikka tayyor.\n\n"
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
        "https://discord.gg/5vBytDqjz"
    )

@dp.message(Command("anonim"))
async def anonim_start(message: types.Message, state: FSMContext):
    await message.answer("✍️ Murojaatingizni yozishingiz mumkin.\n\n📎 Matn, rasm, ovozli xabar yoki fayl yuborishingiz mumkin.")
    await state.set_state(Anonymous.waiting_for_message)

@dp.message(Anonymous.waiting_for_message)
async def get_anonim(message: types.Message, state: FSMContext):
    try:
        caption = "📩 Yangi anonim murojaat"
        if message.text:
            await bot.send_message(ADMIN_ID, f"{caption}:\n\n{message.text}")
        elif message.photo:
            await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption)
        elif message.document:
            await bot.send_document(ADMIN_ID, message.document.file_id, caption=caption)
        elif message.video:
            await bot.send_video(ADMIN_ID, message.video.file_id, caption=caption)
        elif message.voice:
            await bot.send_voice(ADMIN_ID, message.voice.file_id, caption=caption)
        elif message.audio:
            await bot.send_audio(ADMIN_ID, message.audio.file_id, caption=caption)
        elif message.sticker:
            await bot.send_sticker(ADMIN_ID, message.sticker.file_id)
            await bot.send_message(ADMIN_ID, caption)
        else:
            await message.answer("⚠️ Bu turdagi kontent qabul qilinmaydi.")
            return
        await message.answer("✅ Murojaatingiz yuborildi. Rahmat.")
    except Exception:
        await message.answer("❌ Xatolik yuz berdi. Qayta urinib ko'ring.")
    finally:
        await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import logging
import os
import json
import html
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.types import FSInputFile
from dotenv import load_dotenv
from openai import OpenAI

import db

# Env faylidan ma'lumotlarni o'qish
load_dotenv(override=True)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
WELCOME_IMAGE_PATH = r"C:\Users\user\.gemini\antigravity\brain\14a26618-a478-4dad-82b7-44464de2f216\student_bot_welcome_banner_1775422925036.png"

ai_client = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None

dp = Dispatcher()
bot = None

@dp.message(CommandStart())
async def command_start_handler(message: types.Message) -> None:
    # Get referral ID if available in arguments (e.g., /start 123456)
    referrer_id = None
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        referrer_id = int(args[1])
        if referrer_id == message.from_user.id:
            referrer_id = None # Can't refer self
            
    db.add_user(message.from_user.id, referrer_id)
    
    is_admin = str(message.from_user.id) == str(ADMIN_ID)
    is_prem, points = db.get_user_data(message.from_user.id)
    
    # Get bot username for referral link
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
    
    # Passing current points and ref_link to the Web App URL
    webapp_url = "https://ax0724sh-dotcom.github.io/Demo-Bot/"
    params = f"?points={points}&ref_link={ref_link}"
    if is_admin:
        params += "&admin=true"
    
    webapp_url += params
    
    markup = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📱 Asosiy Platforma", web_app=types.WebAppInfo(url=webapp_url))],
            [types.KeyboardButton(text="👤 Profil"), types.KeyboardButton(text="🆘 Yordam")]
        ],
        resize_keyboard=True
    )
    
    status_text = "👑 VIP ADMIN" if is_admin else ("👑 PRO" if is_prem else "⚪️ Standard")
    f_name = html.escape(message.from_user.first_name)
    
    text = (
        f"👋 Assalomu alaykum, <b>{f_name}</b>!\n\n"
        f"🎓 <b>Student Assistant PRO</b> platformasiga xush kelibsiz.\n"
        f"Ushbu tizim orqali siz o'zingizga kerakli materiallarni va Sun'iy Intellekt yordamini olishingiz mumkin.\n\n"
        f"📊 <b>Maqomingiz:</b> <u>{status_text}</u>\n"
        f"💰 <b>Ballaringiz:</b> {points}\n\n"
        f"👇 Boshlash uchun pastdagi tugmani bosing:"
    )
    
    # Send Image with Caption
    if os.path.exists(WELCOME_IMAGE_PATH):
        await message.answer_photo(photo=FSInputFile(WELCOME_IMAGE_PATH), caption=text, reply_markup=markup, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=markup, parse_mode="HTML")

@dp.message(F.text == "👤 Profil")
@dp.message(Command("profile"))
async def profile_handler(message: types.Message):
    is_prem, points = db.get_user_data(message.from_user.id)
    is_admin = str(message.from_user.id) == str(ADMIN_ID)
    status = "👑 VIP ADMIN" if is_admin else ("👑 PRO" if is_prem else "⚪️ Standard")
    f_name = html.escape(message.from_user.full_name)
    
    profile_text = (
        f"👤 <b>Foydalanuvchi Profili</b>\n\n"
        f"🆔 <b>ID:</b> <code>{message.from_user.id}</code>\n"
        f"🏷 <b>Ism:</b> {f_name}\n"
        f"📊 <b>Holati:</b> {status}\n"
        f"💰 <b>Jami Ballar:</b> {points}\n\n"
        f"💡 <i>Ballarni ko'paytirish uchun do'stlarni taklif qiling!</i>"
    )
    await message.answer(profile_text, parse_mode="HTML")

@dp.message(F.text == "🆘 Yordam")
@dp.message(Command("help"))
async def help_handler(message: types.Message):
    help_text = (
        f"🆘 <b>Yordam va Yo'riqnoma</b>\n\n"
        f"1️⃣ <b>Web App:</b> Pastki menyudagi '📱 Asosiy Platforma' tugmasi orqali barcha xizmatlarga kirasiz.\n"
        f"2️⃣ <b>Referal:</b> Do'stlarni taklif qilib ballar to'plang va ularni Premiumga almashtiring.\n"
        f"3️⃣ <b>Premium:</b> Agar to'lov qilgan bo'lsangiz va faollashmasa, adminga murojaat qiling.\n\n"
        f"📞 <b>Admin:</b> @admin_username"
    )
    await message.answer(help_text, parse_mode="HTML")

@dp.message(Command("broadcast"))
async def broadcast_handler(message: types.Message):
    if str(message.from_user.id) != str(ADMIN_ID):
        return
        
    text = message.text.replace("/broadcast", "").strip()
    if not text:
        await message.answer("⚠️ Iltimos, xabar matnini kiriting: <code>/broadcast Xabar...</code>", parse_mode="HTML")
        return
        
    users = db.get_all_users()
    count = 0
    msg = await message.answer(f"🚀 Xabar yuborilmoqda: {len(users)} ta foydalanuvchiga...")
    
    for user_id in users:
        try:
            await bot.send_message(chat_id=user_id, text=text)
            count += 1
            await asyncio.sleep(0.05) # Flood wait prevent
        except Exception:
            pass
            
    await msg.edit_text(f"✅ <b>Bajarildi!</b>\n\nJami yuborildi: {count} ta foydalanuvchiga.", parse_mode="HTML")

@dp.message(F.web_app_data)
async def web_app_data_handler(message: types.Message):
    data = message.web_app_data.data
    try:
        parsed_data = json.loads(data)
        action = parsed_data.get("action")
        
        if action == "generate_ai":
            topic = parsed_data.get("topic", "Noma'lum mavzu")
            loading_msg = await message.answer(f"🤖 <b>AI Referat Rejasini tayyorlamoqda...</b>\n\nMavzu: <code>{html.escape(topic)}</code>", parse_mode="HTML")
            
            if not ai_client:
                await loading_msg.edit_text("❌ AI kaliti o'rnatilmagan. Iltimos, adminga murojaat qiling.")
                return
            
            try:
                response = ai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Sen talabalarga referat va kurs ishlari uchun professional reja tuzib beruvchi yordamchisan. Faqat reja (outline) qaytar, o'zbek tilida."},
                        {"role": "user", "content": f"'{topic}' mavzusida mutlaqo professional referat rejasi tuzib ber."}
                    ]
                )
                ai_text = html.escape(response.choices[0].message.content)
                await loading_msg.edit_text(f"📋 <b>'{html.escape(topic)}' uchun professional reja:</b>\n\n{ai_text}", parse_mode="HTML")
            except Exception as e:
                await loading_msg.edit_text(f"❌ AI bilan bog'lanishda xatolik yuz berdi: {str(e)}")

        if action == "payment_sent":
            plan = parsed_data.get("plan", "Unknown Plan")
            await message.answer("⌛️ <b>To'lov holati tekshirilmoqda...</b>\n\nSizning so'rovingiz tizim administratoriga yetkazildi. Odatda tasdiqlash 2-5 daqiqa vaqt oladi.", parse_mode="HTML")
            
            if ADMIN_ID:
                admin_markup = types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_{message.from_user.id}"),
                            types.InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{message.from_user.id}")
                        ]
                    ]
                )
                admin_text = (
                    f"💳 <b>YANGI TO'LOV SO'ROVI</b>\n\n"
                    f"👤 <b>Foydalanuvchi:</b> {html.escape(message.from_user.full_name)} (@{message.from_user.username})\n"
                    f"🆔 <b>ID:</b> <code>{message.from_user.id}</code>\n"
                    f"📦 <b>Xarid turi:</b> {plan}\n\n"
                    f"⚠️ <i>Pulingiz kartaga tushganligini ilova orqali tekshiring va tasdiqlang.</i>"
                )
                await bot.send_message(chat_id=ADMIN_ID, text=admin_text, reply_markup=admin_markup, parse_mode="HTML")
    except Exception as e:
        print("Xatolik Web App data:", e)

@dp.callback_query(F.data.startswith("approve_"))
async def approve_payment_cb(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    db.set_premium(user_id, True)
    await callback.message.edit_text(callback.message.text + "\n\n✅ <b>HOLAT: TASDIQLANDI</b>", parse_mode="HTML")
    try:
        await bot.send_message(chat_id=user_id, text="🎉 <b>Tabriklaymiz! To'lovingiz muvaffaqiyatli tasdiqlandi.</b>\n\nBotingiz endi PREMIUM darajasida!", parse_mode="HTML")
    except Exception: pass

@dp.callback_query(F.data.startswith("reject_"))
async def reject_payment_cb(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    await callback.message.edit_text(callback.message.text + "\n\n❌ <b>HOLAT: RAD ETILDI</b>", parse_mode="HTML")
    try:
        await bot.send_message(chat_id=user_id, text="❌ <b>Kechirasiz, sizning to'lovingiz admin tomonidan tasdiqlanmadi.</b>", parse_mode="HTML")
    except Exception: pass

async def main() -> None:
    global bot
    db.init_db()
    if not BOT_TOKEN: return
    bot = Bot(token=BOT_TOKEN)
    print("Bot PRO rejimida ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

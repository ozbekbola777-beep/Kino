from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database import get_movie_by_code, search_movies_by_name, search_movies_by_genre
from keyboards import main_menu_keyboard, search_results_keyboard, genre_keyboard
from states import UserState
from handler_start import send_movie
import config

router = Router()

MENU_TEXTS = {
    "🔍 Kino qidirish", "📂 Janrlar",
    "📋 Buyurtma", "📣 Reklama", "ℹ️ Haqida",
}

ORDER_TEXT = (
    "📋 <b>Kino buyurtma qilish</b>\n\n"
    "Izlagan kinoyingiz botda yo'qmi?\n"
    "Quyidagi formatda yuboring:\n"
    "<code>Kino nomi: ...\nTil: O'zbek / Rus</code>\n\n"
    "👤 Admin: @kino_sfera_admin\n"
    "📢 Kanal: @kino_sfera_uz"
)

ADS_TEXT = (
    "📣 <b>Reklama joylashtirish</b>\n\n"
    "Botimizda har kuni yuzlab faol foydalanuvchilar!\n"
    "Narx va shartlar uchun:\n\n"
    "👤 @kino_sfera_admin"
)

ABOUT_TEXT = (
    "ℹ️ <b>Bot haqida</b>\n\n"
    "🎬 <b>Sfera Kino</b> — kinolarni toping!\n\n"
    "✅ O'zbek tilidagi kinolar\n"
    "🔍 Kod yoki nom orqali qidirish\n"
    "📂 Janr bo'yicha ko'rish\n"
    "🆕 Har kuni yangi kinolar\n\n"
    "📢 @kino_sfera_uz\n"
    "👤 @kino_sfera_admin"
)


@router.message(F.text == "🔍 Kino qidirish")
async def search_btn(message: Message, state: FSMContext):
    await state.set_state(UserState.waiting_code)
    await message.answer(
        "🔍 Kino kodini yoki nomini yuboring:\n\n"
        "📌 Kodlar: 👉 @kino_sfera_uz"
    )


@router.message(F.text == "📋 Buyurtma")
async def order_btn(message: Message):
    await message.answer(ORDER_TEXT, parse_mode="HTML")


@router.message(F.text == "📣 Reklama")
async def ads_btn(message: Message):
    await message.answer(ADS_TEXT, parse_mode="HTML")


@router.message(F.text == "ℹ️ Haqida")
async def about_btn(message: Message):
    await message.answer(ABOUT_TEXT, parse_mode="HTML")


@router.message(F.text == "📂 Janrlar")
async def genres_btn(message: Message):
    await message.answer("📂 Janrni tanlang:", reply_markup=genre_keyboard())


@router.callback_query(F.data.startswith("genre_"))
async def genre_selected(call: CallbackQuery):
    genre = call.data.replace("genre_", "")
    movies = await search_movies_by_genre(genre)
    if not movies:
        await call.answer("❌ Bu janrda hozircha kino yo'q.", show_alert=True)
        return
    movie_list = "\n".join([
        f"{i}. {m['name']} — <code>{m['code']}</code>"
        for i, m in enumerate(movies[:10], 1)
    ])
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer(
        f"🔍 <b>{len(movies)} ta natija:</b>\n\n{movie_list}",
        parse_mode="HTML",
        reply_markup=search_results_keyboard(movies)
    )


@router.message(UserState.waiting_code)
async def receive_code(message: Message, state: FSMContext, bot: Bot):
    if not message.text or message.text in MENU_TEXTS:
        return

    if message.text == "❌ Bekor qilish":
        await message.answer(
            "🎬 Kino kodini yuboring:\n\n📌 Kodlar: 👉 @kino_sfera_uz",
            reply_markup=main_menu_keyboard()
        )
        return

    query = message.text.strip()

    # Avval kod bo'yicha qidirish
    movie = await get_movie_by_code(query)
    if movie:
        await send_movie(message, bot, query, state)
        return

    # Nom bo'yicha qidirish
    results = await search_movies_by_name(query)
    if not results:
        await message.answer(
            "❌ Kino topilmadi.\n\n"
            "📌 Kodlarni bu yerdan toping: 👉 @kino_sfera_uz"
        )
        return

    if len(results) == 1:
        await send_movie(message, bot, results[0]["code"], state)
        return

    movie_list = "\n".join([
        f"{i}. {m['name']} — <code>{m['code']}</code>"
        for i, m in enumerate(results[:10], 1)
    ])
    await message.answer(
        f"🔍 <b>{len(results)} ta natija topildi:</b>\n\n{movie_list}",
        parse_mode="HTML",
        reply_markup=search_results_keyboard(results)
    )


@router.callback_query(F.data.startswith("pick_"))
async def pick_movie(call: CallbackQuery, state: FSMContext, bot: Bot):
    code = call.data.replace("pick_", "")
    await call.message.edit_reply_markup(reply_markup=None)
    await send_movie(call.message, bot, code, state)

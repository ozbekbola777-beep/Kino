from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from database import get_active_channels, save_user, is_new_user, mark_greeted, get_movie_by_code
from keyboards import subscribe_keyboard, main_menu_keyboard
from states import UserState
import config

router = Router()

WELCOME_TEXT = (
    "🎬 <b>Sfera Kino botiga xush kelibsiz!</b>\n\n"
    "Bu bot orqali minglab kino va seriallarni topasiz.\n\n"
    "📌 <b>Qanday ishlaydi?</b>\n"
    "Har bir kinoning o'z <b>kodi</b> bor.\n"
    "Kodni kanaldan toping: 👉 @kino_sfera_uz\n\n"
    "Kodni botga yuboring — kino keladi! 🚀"
)

SEND_CODE_TEXT = (
    "🎬 Kino kodini yuboring:\n\n"
    "📌 Kodlar: 👉 @kino_sfera_uz"
)

MOVIE_FOOTER = "📌 Ko'proq kinolar: 👉 @kino_sfera_uz"


async def check_subscription(bot: Bot, user_id: int) -> bool:
    channels = await get_active_channels()
    all_ch = list(channels)
    ids = [c[0] for c in all_ch]
    if config.CHANNEL_ID not in ids and config.CHANNEL_ID != 0:
        all_ch.insert(0, (config.CHANNEL_ID, config.CHANNEL_USERNAME))
    for ch_id, _ in all_ch:
        if ch_id == 0:
            continue
        try:
            member = await bot.get_chat_member(ch_id, user_id)
            if member.status in ("left", "kicked", "banned"):
                return False
        except Exception:
            pass
    return True


async def show_menu(target, state: FSMContext):
    await state.set_state(UserState.waiting_code)
    await target.answer(SEND_CODE_TEXT, reply_markup=main_menu_keyboard())


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    user_id = message.from_user.id

    # Deep link tekshirish
    args = message.text.split()
    deep_code = args[1] if len(args) > 1 else None
    if deep_code:
        await state.update_data(deep_code=deep_code)

    # Obuna tekshirish
    if not await check_subscription(bot, user_id):
        channels = await get_active_channels()
        all_ch = list(channels)
        ids = [c[0] for c in all_ch]
        if config.CHANNEL_ID not in ids and config.CHANNEL_ID != 0:
            all_ch.insert(0, (config.CHANNEL_ID, config.CHANNEL_USERNAME))
        ch_list = "\n".join([f"👉 {c[1]}" for c in all_ch if c[0] != 0])
        await message.answer(
            f"📢 Botdan foydalanish uchun obuna bo'ling:\n\n{ch_list}",
            reply_markup=subscribe_keyboard(all_ch)
        )
        return

    new_user = await is_new_user(user_id)
    await save_user(user_id, message.from_user.username)

    if new_user:
        await message.answer(WELCOME_TEXT, parse_mode="HTML")
        await mark_greeted(user_id)

    data = await state.get_data()
    code = data.get("deep_code")
    if code:
        await state.update_data(deep_code=None)
        await send_movie(message, bot, code, state)
        return

    await show_menu(message, state)


@router.callback_query(F.data == "check_sub")
async def check_sub_callback(call: CallbackQuery, state: FSMContext, bot: Bot):
    user_id = call.from_user.id
    if not await check_subscription(bot, user_id):
        await call.answer("❌ Hali obuna bo'lmagansiz!", show_alert=True)
        return
    await call.message.edit_reply_markup(reply_markup=None)

    new_user = await is_new_user(user_id)
    await save_user(user_id, call.from_user.username)

    if new_user:
        await call.message.answer(WELCOME_TEXT, parse_mode="HTML")
        await mark_greeted(user_id)

    data = await state.get_data()
    code = data.get("deep_code")
    if code:
        await state.update_data(deep_code=None)
        await send_movie(call.message, bot, code, state)
        return

    await show_menu(call.message, state)


async def send_movie(target, bot: Bot, code: str, state: FSMContext):
    movie = await get_movie_by_code(code)
    if not movie:
        await target.answer(
            "❌ Kino topilmadi. Kodni tekshirib qayta urinib ko'ring.",
            reply_markup=main_menu_keyboard()
        )
        await state.set_state(UserState.waiting_code)
        return
    try:
        await target.answer("🎬 Mana sizning kinoyingiz:")
        await bot.forward_message(
            chat_id=target.chat.id,
            from_chat_id=config.STORAGE_GROUP_ID,
            message_id=movie["group_msg_id"]
        )
        await bot.send_message(
            chat_id=target.chat.id,
            text=f"🎬 <b>{movie['name']}</b>\n\n{MOVIE_FOOTER}",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard()
        )
    except Exception as e:
        await target.answer(f"⚠️ Xato: {e}")
    await state.set_state(UserState.waiting_code)

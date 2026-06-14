import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from database import (
    add_movie, delete_movie, add_admin, remove_admin,
    add_channel, get_all_admins, get_all_user_ids, get_user_count
)
from keyboards import (
    admin_panel_keyboard, super_admin_panel_keyboard,
    cancel_keyboard, movie_channel_keyboard,
    main_menu_keyboard, genre_select_keyboard,
    broadcast_confirm_keyboard
)
from states import (
    AddMovieState, AddAdminState, RemoveAdminState,
    AddChannelState, DeleteMovieState, BroadcastState
)
import config

router = Router()


def is_admin(uid): return uid in config.ADMIN_IDS
def is_super(uid): return uid in config.SUPER_ADMIN_IDS
def is_cancel(text): return text == "❌ Bekor qilish"


async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=main_menu_keyboard())


# ── /admin ────────────────────────────────────────────────────
@router.message(Command("admin"))
async def admin_cmd(message: Message):
    uid = message.from_user.id
    if is_super(uid):
        await message.answer("⚡️ Super Admin panel:", reply_markup=super_admin_panel_keyboard())
    elif is_admin(uid):
        await message.answer("🔧 Admin panel:", reply_markup=admin_panel_keyboard())


@router.callback_query(F.data == "admin_close")
async def admin_close(call: CallbackQuery):
    await call.message.delete()


# ── Statistika ────────────────────────────────────────────────
@router.callback_query(F.data == "admin_stats")
async def admin_stats(call: CallbackQuery):
    if not is_super(call.from_user.id):
        return
    count = await get_user_count()
    admins = await get_all_admins()
    admin_list = "\n".join([
        f"{'⭐' if a[2] else '👤'} {a[1] or 'Nomsiz'} — <code>{a[0]}</code>"
        for a in admins
    ]) or "—"
    await call.message.answer(
        f"📊 <b>Statistika</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{count}</b>\n\n"
        f"👮 Adminlar:\n{admin_list}",
        parse_mode="HTML"
    )


# ── Broadcast ─────────────────────────────────────────────────
@router.callback_query(F.data == "admin_broadcast")
async def start_broadcast(call: CallbackQuery, state: FSMContext):
    if not is_super(call.from_user.id):
        return
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer(
        "📣 Broadcast xabarini yuboring:", reply_markup=cancel_keyboard()
    )
    await state.set_state(BroadcastState.waiting_message)


@router.message(BroadcastState.waiting_message)
async def broadcast_preview(message: Message, state: FSMContext):
    if is_cancel(message.text or ""):
        await cancel(message, state)
        return
    await state.update_data(
        bc_text=message.text,
        bc_photo=message.photo[-1].file_id if message.photo else None,
        bc_video=message.video.file_id if message.video else None,
        bc_caption=message.caption
    )
    count = await get_user_count()
    await message.answer(
        f"📣 <b>{count}</b> ta foydalanuvchiga yuboriladi. Tasdiqlaysizmi?",
        parse_mode="HTML",
        reply_markup=broadcast_confirm_keyboard()
    )
    await state.set_state(BroadcastState.confirm)


@router.callback_query(F.data == "broadcast_confirm", BroadcastState.confirm)
async def broadcast_send(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()
    await call.message.edit_reply_markup(reply_markup=None)
    user_ids = await get_all_user_ids()
    sent = failed = 0
    total = len(user_ids)
    status = await call.message.answer(f"⏳ 0/{total}")
    for i, uid in enumerate(user_ids):
        try:
            if data.get("bc_photo"):
                await bot.send_photo(uid, data["bc_photo"], caption=data.get("bc_caption"), parse_mode="HTML")
            elif data.get("bc_video"):
                await bot.send_video(uid, data["bc_video"], caption=data.get("bc_caption"), parse_mode="HTML")
            else:
                await bot.send_message(uid, data["bc_text"], parse_mode="HTML")
            sent += 1
        except Exception:
            failed += 1
        if (i + 1) % 25 == 0:
            try:
                await status.edit_text(f"⏳ {i+1}/{total}")
            except Exception:
                pass
        await asyncio.sleep(0.05)
    await status.edit_text(f"✅ Tugadi! Yuborildi: {sent} | Xato: {failed}")


@router.callback_query(F.data == "broadcast_cancel", BroadcastState.confirm)
async def broadcast_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer("❌ Broadcast bekor qilindi.")


# ── Kino qo'shish ─────────────────────────────────────────────
@router.callback_query(F.data == "admin_add_movie")
async def start_add_movie(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer(
        "📝 Kino nomini yuboring:", reply_markup=cancel_keyboard()
    )
    await state.set_state(AddMovieState.name)


@router.message(AddMovieState.name)
async def movie_name(message: Message, state: FSMContext):
    if is_cancel(message.text or ""):
        await cancel(message, state)
        return
    if not message.text:
        await message.answer("❗ Faqat matn yuboring:", reply_markup=cancel_keyboard())
        return
    await state.update_data(name=message.text.strip())
    await message.answer("🔢 Kino kodini yuboring (masalan: 001):", reply_markup=cancel_keyboard())
    await state.set_state(AddMovieState.code)


@router.message(AddMovieState.code)
async def movie_code(message: Message, state: FSMContext):
    if is_cancel(message.text or ""):
        await cancel(message, state)
        return
    if not message.text:
        await message.answer("❗ Faqat matn yuboring:", reply_markup=cancel_keyboard())
        return
    code = message.text.strip().upper()
    from database import get_movie_by_code
    if await get_movie_by_code(code):
        await message.answer(
            f"⚠️ <code>{code}</code> kodi allaqachon mavjud! Boshqa kod kiriting:",
            parse_mode="HTML", reply_markup=cancel_keyboard()
        )
        return
    await state.update_data(code=code)
    await message.answer(
        "📂 Janrlarni tanlang (bir nechta mumkin):",
        reply_markup=genre_select_keyboard([])
    )
    await state.set_state(AddMovieState.genres)


@router.callback_query(F.data.startswith("genresel_"), AddMovieState.genres)
async def genre_toggle(call: CallbackQuery, state: FSMContext):
    key = call.data.replace("genresel_", "")
    if key == "done":
        data = await state.get_data()
        selected = data.get("selected_genres", [])
        if not selected:
            await call.answer("❗ Kamida 1ta janr tanlang!", show_alert=True)
            return
        await state.update_data(genres=",".join(selected))
        await call.message.edit_reply_markup(reply_markup=None)
        await call.message.answer(
            "🎬 Kino faylini yuboring (faqat VIDEO):", reply_markup=cancel_keyboard()
        )
        await state.set_state(AddMovieState.movie_file)
        return
    data = await state.get_data()
    selected = data.get("selected_genres", [])
    if key in selected:
        selected.remove(key)
    else:
        selected.append(key)
    await state.update_data(selected_genres=selected)
    await call.message.edit_reply_markup(reply_markup=genre_select_keyboard(selected))
    await call.answer()


@router.message(AddMovieState.movie_file, F.video)
async def movie_file(message: Message, state: FSMContext, bot: Bot):
    try:
        sent = await bot.forward_message(
            chat_id=config.STORAGE_GROUP_ID,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )
        await state.update_data(group_msg_id=sent.message_id)
    except Exception as e:
        await message.answer(
            f"⚠️ Guruhga yuborishda xato: {e}\nQayta yuboring:",
            reply_markup=cancel_keyboard()
        )
        return
    await message.answer(
        "🎞 Kino posteri/trailerni yuboring (VIDEO yoki RASM):",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(AddMovieState.clip)


@router.message(AddMovieState.movie_file)
async def movie_file_wrong(message: Message):
    if is_cancel(message.text or ""):
        return
    await message.answer("❗ Faqat <b>VIDEO</b> fayl yuboring!", parse_mode="HTML", reply_markup=cancel_keyboard())


@router.message(AddMovieState.clip, F.video | F.photo)
async def movie_clip(message: Message, state: FSMContext):
    if message.video:
        await state.update_data(clip_type="video", clip_file_id=message.video.file_id)
    else:
        await state.update_data(clip_type="photo", clip_file_id=message.photo[-1].file_id)
    await message.answer("📄 Kino haqida qisqacha tavsif yuboring:", reply_markup=cancel_keyboard())
    await state.set_state(AddMovieState.description)


@router.message(AddMovieState.clip)
async def movie_clip_wrong(message: Message):
    if is_cancel(message.text or ""):
        return
    await message.answer("❗ <b>VIDEO</b> yoki <b>RASM</b> yuboring!", parse_mode="HTML", reply_markup=cancel_keyboard())


@router.message(AddMovieState.description)
async def movie_description(message: Message, state: FSMContext, bot: Bot):
    if is_cancel(message.text or ""):
        await cancel(message, state)
        return
    if not message.text:
        await message.answer("❗ Faqat matn yuboring:", reply_markup=cancel_keyboard())
        return
    await state.update_data(description=message.text.strip())
    data = await state.get_data()
    await state.clear()

    code = data["code"]
    name = data["name"]
    genres = data.get("genres", "")
    group_msg_id = data["group_msg_id"]
    clip_type = data["clip_type"]
    clip_file_id = data["clip_file_id"]
    description = data["description"]

    wait = await message.answer("⏳ Kanalga yuklanmoqda...")
    bot_info = await bot.get_me()
    keyboard = movie_channel_keyboard(code, bot_info.username)
    caption = f"🎬 <b>{name}</b>\n🔑 Kod: <code>{code}</code>\n\n{description}"

    channel_msg_id = None
    try:
        if clip_type == "video":
            sent = await bot.send_video(
                config.CHANNEL_ID, video=clip_file_id,
                caption=caption, parse_mode="HTML", reply_markup=keyboard
            )
        else:
            sent = await bot.send_photo(
                config.CHANNEL_ID, photo=clip_file_id,
                caption=caption, parse_mode="HTML", reply_markup=keyboard
            )
        channel_msg_id = sent.message_id
    except Exception as e:
        await message.answer(f"⚠️ Kanalga yuborishda xato: {e}")

    await add_movie(code, name, description, genres, group_msg_id, channel_msg_id)

    try:
        await wait.delete()
    except Exception:
        pass

    await message.answer(
        f"✅ Kino qo'shildi!\n\n"
        f"🎬 <b>{name}</b>\n🔑 <code>{code}</code>\n📂 {genres}",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard()
    )


# ── Kino o'chirish ────────────────────────────────────────────
@router.callback_query(F.data == "admin_del_movie")
async def start_del_movie(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer("🗑 O'chirish uchun kino kodini yuboring:", reply_markup=cancel_keyboard())
    await state.set_state(DeleteMovieState.waiting_code)


@router.message(DeleteMovieState.waiting_code)
async def delete_movie_handler(message: Message, state: FSMContext, bot: Bot):
    if is_cancel(message.text or ""):
        await cancel(message, state)
        return
    if not message.text:
        await message.answer("❗ Kino kodini matn ko'rinishida yuboring:")
        return
    code = message.text.strip().upper()
    result = await delete_movie(code)
    if not result:
        await message.answer(f"❌ <code>{code}</code> topilmadi.", parse_mode="HTML")
        await state.clear()
        return
    errors = []
    if result["group_msg_id"]:
        try:
            await bot.delete_message(config.STORAGE_GROUP_ID, result["group_msg_id"])
        except Exception as e:
            errors.append(f"Guruh: {e}")
    if result["channel_msg_id"]:
        try:
            await bot.delete_message(config.CHANNEL_ID, result["channel_msg_id"])
        except Exception as e:
            errors.append(f"Kanal: {e}")
    msg = f"✅ <code>{code}</code> o'chirildi."
    if errors:
        msg += "\n⚠️ " + "\n".join(errors)
    await message.answer(msg, parse_mode="HTML", reply_markup=main_menu_keyboard())
    await state.clear()


# ── Admin qo'shish ────────────────────────────────────────────
@router.callback_query(F.data == "admin_add_admin")
async def start_add_admin(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer(
        "👤 Yangi admin <b>user_id</b> sini yuboring:\n"
        "❗ Faqat raqam (masalan: <code>123456789</code>)",
        parse_mode="HTML", reply_markup=cancel_keyboard()
    )
    await state.set_state(AddAdminState.waiting_id)


@router.message(AddAdminState.waiting_id)
async def add_admin_handler(message: Message, state: FSMContext):
    if is_cancel(message.text or ""):
        await cancel(message, state)
        return
    if not message.text or not message.text.strip().lstrip('-').isdigit():
        await message.answer(
            "❌ Noto'g'ri format. Faqat raqam kiriting:",
            reply_markup=cancel_keyboard()
        )
        return
    uid = int(message.text.strip())
    await add_admin(uid, "", is_super=0)
    if uid not in config.ADMIN_IDS:
        config.ADMIN_IDS.append(uid)
    await message.answer(
        f"✅ Admin qo'shildi: <code>{uid}</code>",
        parse_mode="HTML", reply_markup=main_menu_keyboard()
    )
    await state.clear()


# ── Admin o'chirish ───────────────────────────────────────────
@router.callback_query(F.data == "admin_remove_admin")
async def start_remove_admin(call: CallbackQuery, state: FSMContext):
    if not is_super(call.from_user.id):
        return
    admins = await get_all_admins()
    admin_list = "\n".join([
        f"{'⭐' if a[2] else '👤'} <code>{a[0]}</code> {a[1] or ''}"
        for a in admins
    ]) or "Admin yo'q"
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer(
        f"Adminlar:\n{admin_list}\n\nO'chirish uchun ID yuboring:",
        parse_mode="HTML", reply_markup=cancel_keyboard()
    )
    await state.set_state(RemoveAdminState.waiting_id)


@router.message(RemoveAdminState.waiting_id)
async def remove_admin_handler(message: Message, state: FSMContext):
    if is_cancel(message.text or ""):
        await cancel(message, state)
        return
    if not message.text or not message.text.strip().lstrip('-').isdigit():
        await message.answer("❌ Noto'g'ri format. Faqat raqam:", reply_markup=cancel_keyboard())
        return
    uid = int(message.text.strip())
    if uid in config.SUPER_ADMIN_IDS:
        await message.answer("❌ Super adminni o'chirib bo'lmaydi.")
        await state.clear()
        return
    await remove_admin(uid)
    if uid in config.ADMIN_IDS:
        config.ADMIN_IDS.remove(uid)
    await message.answer(
        f"✅ Admin o'chirildi: <code>{uid}</code>",
        parse_mode="HTML", reply_markup=main_menu_keyboard()
    )
    await state.clear()


# ── Kanal qo'shish ────────────────────────────────────────────
@router.callback_query(F.data == "admin_add_channel")
async def start_add_channel(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer(
        "📢 Kanal username va ID yuboring:\n<code>@username -100xxxxxxxxxx</code>",
        parse_mode="HTML", reply_markup=cancel_keyboard()
    )
    await state.set_state(AddChannelState.waiting_channel)


@router.message(AddChannelState.waiting_channel)
async def add_channel_handler(message: Message, state: FSMContext):
    if is_cancel(message.text or ""):
        await cancel(message, state)
        return
    try:
        parts = message.text.strip().split()
        username, ch_id = parts[0], int(parts[1])
        await add_channel(ch_id, username)
        await message.answer(f"✅ Kanal qo'shildi: {username}", reply_markup=main_menu_keyboard())
        await state.clear()
    except Exception:
        await message.answer(
            "❌ Format noto'g'ri:\n<code>@username -100xxxxxxxxxx</code>",
            parse_mode="HTML", reply_markup=cancel_keyboard()
        )

from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
import config


def main_menu_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🔍 Kino qidirish")],
        [KeyboardButton(text="📂 Janrlar"), KeyboardButton(text="📋 Buyurtma")],
        [KeyboardButton(text="📣 Reklama"), KeyboardButton(text="ℹ️ Haqida")],
    ], resize_keyboard=True)


def cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def subscribe_keyboard(channels: list):
    buttons = []
    for ch_id, ch_username in channels:
        buttons.append([InlineKeyboardButton(
            text=f"📢 {ch_username}",
            url=f"https://t.me/{ch_username.lstrip('@')}"
        )])
    buttons.append([InlineKeyboardButton(
        text="✅ Obuna bo'ldim, tekshirish",
        callback_data="check_sub"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def genre_keyboard():
    buttons = []
    row = []
    for i, (key, label) in enumerate(config.GENRES):
        row.append(InlineKeyboardButton(
            text=label, callback_data=f"genre_{key}"
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def genre_select_keyboard(selected: list):
    buttons = []
    row = []
    for key, label in config.GENRES:
        check = "✅ " if key in selected else ""
        row.append(InlineKeyboardButton(
            text=f"{check}{label}",
            callback_data=f"genresel_{key}"
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(
        text="✅ Tayyor", callback_data="genresel_done"
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def movie_channel_keyboard(code: str, bot_username: str):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🎬 Kinoni olish",
            url=f"https://t.me/{bot_username}?start={code}"
        )
    ]])


def search_results_keyboard(movies: list):
    buttons = []
    for i, m in enumerate(movies[:10], 1):
        buttons.append([InlineKeyboardButton(
            text=f"{i}. {m['name']}",
            callback_data=f"pick_{m['code']}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_panel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Kino qo'shish", callback_data="admin_add_movie")],
        [InlineKeyboardButton(text="🗑 Kino o'chirish", callback_data="admin_del_movie")],
        [InlineKeyboardButton(text="👤 Admin qo'shish", callback_data="admin_add_admin")],
        [InlineKeyboardButton(text="📢 Kanal qo'shish", callback_data="admin_add_channel")],
        [InlineKeyboardButton(text="❌ Yopish", callback_data="admin_close")],
    ])


def super_admin_panel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Kino qo'shish", callback_data="admin_add_movie")],
        [InlineKeyboardButton(text="🗑 Kino o'chirish", callback_data="admin_del_movie")],
        [InlineKeyboardButton(text="👤 Admin qo'shish", callback_data="admin_add_admin")],
        [InlineKeyboardButton(text="🚫 Admin o'chirish", callback_data="admin_remove_admin")],
        [InlineKeyboardButton(text="📢 Kanal qo'shish", callback_data="admin_add_channel")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📣 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="❌ Yopish", callback_data="admin_close")],
    ])


def broadcast_confirm_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Yuborish", callback_data="broadcast_confirm"),
        InlineKeyboardButton(text="❌ Bekor", callback_data="broadcast_cancel"),
    ]])

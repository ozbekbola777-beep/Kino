import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

_admin_str = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = list(map(int, _admin_str.split(","))) if _admin_str else []

_super_str = os.getenv("SUPER_ADMIN_IDS", _admin_str)
SUPER_ADMIN_IDS = list(map(int, _super_str.split(","))) if _super_str else []

for _sid in SUPER_ADMIN_IDS:
    if _sid not in ADMIN_IDS:
        ADMIN_IDS.append(_sid)

# Kinolar saqlanadigan guruh (private)
STORAGE_GROUP_ID = int(os.getenv("STORAGE_GROUP_ID", "0"))

# Majburiy obuna kanali
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "0"))
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@kino_sfera_uz")

GENRES = [
    ("action",    "🔫 Jangari"),
    ("comedy",    "😂 Komediya"),
    ("drama",     "🎭 Drama"),
    ("horror",    "👻 Qo'rqinchli"),
    ("fantasy",   "🚀 Fantastik"),
    ("detective", "🔍 Detektiv"),
    ("cartoon",   "🎨 Multfilm"),
    ("romantic",  "💕 Romantik"),
    ("series",    "📺 Serial"),
    ("biography", "🧑 Biografik"),
]

import aiosqlite
import os

DB_PATH = os.getenv("DB_PATH", "kino.db")


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                genres TEXT DEFAULT '',
                group_msg_id INTEGER,
                channel_msg_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT DEFAULT '',
                greeted INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                username TEXT DEFAULT '',
                is_super INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER UNIQUE NOT NULL,
                channel_username TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_code ON movies(code)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_name ON movies(name)")
        await db.commit()


async def is_new_user(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT greeted FROM users WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return row is None or row[0] == 0


async def mark_greeted(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET greeted = 1 WHERE user_id = ?", (user_id,)
        )
        await db.commit()


async def save_user(user_id: int, username: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, username, greeted)
            VALUES (?, ?, 0)
            ON CONFLICT(user_id) DO UPDATE SET username = excluded.username
        """, (user_id, username or ""))
        await db.commit()


async def get_user_count():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cur:
            row = await cur.fetchone()
            return row[0]


async def get_all_user_ids():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT user_id FROM users") as cur:
            rows = await cur.fetchall()
            return [r[0] for r in rows]


async def add_movie(code, name, description, genres, group_msg_id, channel_msg_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO movies (code, name, description, genres, group_msg_id, channel_msg_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (code, name, description, genres, group_msg_id, channel_msg_id))
        await db.commit()


async def get_movie_by_code(code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT * FROM movies WHERE UPPER(code) = UPPER(?)", (code,)
        ) as cur:
            row = await cur.fetchone()
            if row:
                cols = [d[0] for d in cur.description]
                return dict(zip(cols, row))
    return None


async def search_movies_by_name(name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT * FROM movies WHERE LOWER(name) LIKE LOWER(?)",
            (f"%{name}%",)
        ) as cur:
            rows = await cur.fetchall()
            if rows:
                cols = [d[0] for d in cur.description]
                return [dict(zip(cols, r)) for r in rows]
    return []


async def search_movies_by_genre(genre: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT * FROM movies WHERE genres LIKE ?", (f"%{genre}%",)
        ) as cur:
            rows = await cur.fetchall()
            if rows:
                cols = [d[0] for d in cur.description]
                return [dict(zip(cols, r)) for r in rows]
    return []


async def delete_movie(code: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT group_msg_id, channel_msg_id FROM movies WHERE UPPER(code) = UPPER(?)",
            (code,)
        ) as cur:
            row = await cur.fetchone()
        if row:
            await db.execute(
                "DELETE FROM movies WHERE UPPER(code) = UPPER(?)", (code,)
            )
            await db.commit()
            return {"group_msg_id": row[0], "channel_msg_id": row[1]}
    return None


async def add_admin(user_id: int, username: str, is_super: int = 0):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO admins (user_id, username, is_super)
            VALUES (?, ?, ?)
        """, (user_id, username, is_super))
        await db.commit()


async def remove_admin(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM admins WHERE user_id = ?", (user_id,))
        await db.commit()


async def get_all_admins():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_id, username, is_super FROM admins"
        ) as cur:
            return await cur.fetchall()


async def add_channel(channel_id: int, username: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO channels (channel_id, channel_username)
            VALUES (?, ?)
        """, (channel_id, username))
        await db.commit()


async def get_active_channels():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT channel_id, channel_username FROM channels WHERE is_active = 1"
        ) as cur:
            return await cur.fetchall()

import os

import aiosqlite

DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_slots (
                user_id INTEGER PRIMARY KEY,
                slot_1_id INTEGER DEFAULT NULL,
                slot_1_nick TEXT DEFAULT NULL,
                slot_2_id INTEGER DEFAULT NULL,
                slot_2_nick TEXT DEFAULT NULL,
                slot_3_id INTEGER DEFAULT NULL,
                slot_3_nick TEXT DEFAULT NULL
            )
        """)
        await db.commit()

async def get_user_slots(user_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT 
            slot_1_id, slot_1_nick, 
            slot_2_id, slot_2_nick,
            slot_3_id, slot_3_nick
            FROM user_slots WHERE user_id = ?""", 
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "slot_1": {"id": row["slot_1_id"], "nick": row["slot_1_nick"]},
                    "slot_2": {"id": row["slot_2_id"], "nick": row["slot_2_nick"]},
                    "slot_3": {"id": row["slot_3_id"], "nick": row["slot_3_nick"]}
                }
            return {
                "slot_1": {"id": None, "nick": None},
                "slot_2": {"id": None, "nick": None},
                "slot_3": {"id": None, "nick": None}
            }

async def update_user_slot(user_id: int, slot_num: int, account_id: int, nick: str):
    # if slot_num not in:
    #     raise ValueError("Номер слота должен быть от 1 до 3")
    id_column = f"slot_{slot_num}_id"
    nick_column = f"slot_{slot_num}_nick"

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"""
                INSERT INTO user_slots (user_id, {id_column}, {nick_column}) 
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET 
                    {id_column} = excluded.{id_column},
                    {nick_column} = excluded.{nick_column}
            """, 
            (user_id, account_id, nick)
        )
        # await db.execute(
        #     f"UPDATE user_slots SET {id_column} = ?, {nick_column} = ? WHERE user_id = ?", 
        #     (account_id, nick, user_id)
        # )
        await db.commit()

async def close_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.close()
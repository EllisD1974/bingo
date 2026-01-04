import os
import asyncio
import uuid
import random
import asyncpg
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

DATABASE_URL = os.environ["DATABASE_URL"]

app = FastAPI()

db_pool: asyncpg.Pool | None = None

# ---------------- In-memory rooms ----------------
rooms = {}

# ---------------- Database ----------------
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS options (
    id SERIAL PRIMARY KEY,
    text TEXT NOT NULL UNIQUE
);
"""

DEFAULT_OPTIONS = [f"Option {i}" for i in range(1, 101)]


async def wait_for_db(retries: int = 30, delay: float = 2.0):
    """Wait until Postgres is accepting connections."""
    for attempt in range(retries):
        try:
            conn = await asyncpg.connect(DATABASE_URL)
            await conn.close()
            print("✅ Database is ready")
            return
        except Exception as e:
            print(f"⏳ Waiting for database ({attempt + 1}/{retries})...")
            await asyncio.sleep(delay)

    raise RuntimeError("❌ Database did not become ready in time")



async def init_db():
    global db_pool

    await wait_for_db()

    db_pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=1,
        max_size=10,
    )

    async with db_pool.acquire() as conn:
        await conn.execute(CREATE_TABLE_SQL)

        count = await conn.fetchval("SELECT COUNT(*) FROM options")
        if count == 0:
            await conn.executemany(
                "INSERT INTO options(text) VALUES($1) ON CONFLICT DO NOTHING",
                [(item,) for item in DEFAULT_OPTIONS],
            )
            print("✅ Default bingo options inserted")


async def get_all_options():
    if db_pool is None:
        raise RuntimeError("Database pool not initialized")

    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT text FROM options")
        return [r["text"] for r in rows]



# ---------------- Startup ----------------
@app.on_event("startup")
async def startup():
    await init_db()


# ---------------- WebSocket ----------------
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()
    client_id = str(uuid.uuid4())

    room = rooms.setdefault(
        room_id,
        {"clients": {}, "marked": set(), "cards": {}}
    )

    all_options = await get_all_options()
    card = random.sample(all_options, 24)

    room["clients"][client_id] = websocket
    room["cards"][client_id] = card

    await websocket.send_json({
        "type": "init",
        "client_id": client_id,
        "card": card,
        "marked": list(room["marked"]),
    })

    try:
        while True:
            msg = await websocket.receive_json()
            option = msg["option"]
            action = msg["action"]  # "mark" | "unmark"

            if action == "mark":
                room["marked"].add(option)
            else:
                room["marked"].discard(option)

            for cid, ws in room["clients"].items():
                if cid != client_id and option in room["cards"][cid]:
                    await ws.send_json({
                        "type": "update",
                        "option": option,
                        "action": action,
                    })

    except WebSocketDisconnect:
        room["clients"].pop(client_id, None)
        room["cards"].pop(client_id, None)


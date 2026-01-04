import random
import uuid
from pathlib import Path
from typing import Dict, Set, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

# ---------- Config ----------
OPTIONS_FILE = Path("bingo_options.txt")
CARD_SIZE = 24

# ---------- Load options ----------
ALL_OPTIONS = [
    line.strip()
    for line in OPTIONS_FILE.read_text(encoding="utf-8").splitlines()
    if line.strip()
]

if len(ALL_OPTIONS) < CARD_SIZE:
    raise RuntimeError("Not enough bingo options in file")

# ---------- App ----------
app = FastAPI(title="Multiplayer Bingo API")

# ---------- In-memory state ----------
class Client:
    def __init__(self, ws: WebSocket, card: List[str]):
        self.ws = ws
        self.card = card


class Room:
    def __init__(self):
        self.clients: Dict[str, Client] = {}
        self.marked: Set[str] = set()


rooms: Dict[str, Room] = {}


# ---------- Helpers ----------
def get_room(room_id: str) -> Room:
    if room_id not in rooms:
        rooms[room_id] = Room()
    return rooms[room_id]


async def broadcast(room: Room, message: dict):
    for client in room.clients.values():
        await client.ws.send_json(message)


# ---------- WebSocket endpoint ----------
# @app.websocket("/ws/{room_id}")
# async def bingo_ws(ws: WebSocket, room_id: str):
#     await ws.accept()
#
#     room = get_room(room_id)
#     client_id = str(uuid.uuid4())
#
#     # Generate bingo card for this client
#     card = random.sample(ALL_OPTIONS, CARD_SIZE)
#
#     room.clients[client_id] = Client(ws, card)
#
#     # Send initial state
#     await ws.send_json({
#         "type": "init",
#         "client_id": client_id,
#         "card": card,
#         "marked": list(room.marked),
#     })
#
#     try:
#         while True:
#             msg = await ws.receive_json()
#
#             if msg["type"] == "mark":
#                 option = msg["option"]
#                 room.marked.add(option)
#
#                 await broadcast(room, {
#                     "type": "update",
#                     "action": "mark",
#                     "option": option,
#                 })
#
#             elif msg["type"] == "unmark":
#                 option = msg["option"]
#                 room.marked.discard(option)
#
#                 await broadcast(room, {
#                     "type": "update",
#                     "action": "unmark",
#                     "option": option,
#                 })
#
#     except WebSocketDisconnect:
#         room.clients.pop(client_id, None)
#
#         # Optional cleanup
#         if not room.clients:
#             rooms.pop(room_id, None)
@app.websocket("/ws/{room_id}")
async def bingo_ws(ws: WebSocket, room_id: str):
    await ws.accept()

    room = get_room(room_id)
    client_id = str(uuid.uuid4())
    card = random.sample(ALL_OPTIONS, CARD_SIZE)

    room.clients[client_id] = Client(ws, card)

    await ws.send_json({
        "type": "init",
        "card": card,
        "marked": list(room.marked),
    })

    try:
        while True:
            msg = await ws.receive_json()

            option = msg["option"]

            if msg["type"] == "mark":
                room.marked.add(option)
                await broadcast(room, {
                    "type": "update",
                    "action": "mark",
                    "option": option,
                })

            elif msg["type"] == "unmark":
                room.marked.discard(option)
                await broadcast(room, {
                    "type": "update",
                    "action": "unmark",
                    "option": option,
                })

    except WebSocketDisconnect:
        room.clients.pop(client_id, None)



# import os
# import asyncio
# import uuid
# import random
# import asyncpg
# from fastapi import FastAPI, WebSocket, WebSocketDisconnect
#
# # ---------------- Environment ----------------
# DATABASE_URL = os.environ.get(
#     "DATABASE_URL",
#     "postgresql://localhost:bingo@bingo:5432/bingo"  # fallback
# )
# DATABASE_URL = "postgresql://localhost:bingo@bingo:5432/bingo"
#
# app = FastAPI()
#
# # ---------------- In-memory rooms ----------------
# # {room_id: {"clients": {client_id: websocket}, "marked": set(), "cards": {client_id: [options]}}}
# rooms = {}
#
# # ---------------- Database helpers ----------------
# async def init_db():
#     """Create tables if they don't exist, and populate default options."""
#     conn = await asyncpg.connect(DATABASE_URL)
#     await conn.execute("""
#         CREATE TABLE IF NOT EXISTS options (
#             id SERIAL PRIMARY KEY,
#             text TEXT NOT NULL UNIQUE
#         )
#     """)
#     # populate default options if empty
#     count = await conn.fetchval("SELECT COUNT(*) FROM options")
#     if count == 0:
#         default_items = [f"Option {i}" for i in range(1, 101)]
#         for item in default_items:
#             await conn.execute("INSERT INTO options(text) VALUES($1) ON CONFLICT DO NOTHING", item)
#     await conn.close()
#
# async def get_all_options():
#     """Fetch all bingo options from the database."""
#     conn = await asyncpg.connect(DATABASE_URL)
#     rows = await conn.fetch("SELECT text FROM options")
#     await conn.close()
#     return [row["text"] for row in rows]
#
# # ---------------- Startup ----------------
# # @app.on_event("startup")
# async def startup():
#     """Initialize database on startup."""
#     await init_db()
#
# # ---------------- WebSocket ----------------
# @app.websocket("/ws/{room_id}")
# async def websocket_endpoint(websocket: WebSocket, room_id: str):
#     await websocket.accept()
#     client_id = str(uuid.uuid4())
#
#     # get room or create
#     room = rooms.setdefault(room_id, {"clients": {}, "marked": set(), "cards": {}})
#
#     # pick 24 random options from DB
#     all_options = await get_all_options()
#     card = random.sample(all_options, 24)
#     room["cards"][client_id] = card
#     room["clients"][client_id] = websocket
#
#     # send initial card + marked items
#     await websocket.send_json({
#         "type": "init",
#         "client_id": client_id,
#         "card": card,
#         "marked": list(room["marked"])
#     })
#
#     try:
#         while True:
#             data = await websocket.receive_json()
#             option = data["option"]
#             action = data["type"]  # "mark" or "unmark"
#
#             # update room state
#             if action == "mark":
#                 room["marked"].add(option)
#             else:
#                 room["marked"].discard(option)
#
#             # broadcast to all other clients in the room who have this option
#             for cid, ws in room["clients"].items():
#                 if ws == websocket:
#                     continue
#                 if option in room["cards"][cid]:
#                     await ws.send_json({
#                         "type": "update",
#                         "option": option,
#                         "action": action
#                     })
#
#     except WebSocketDisconnect:
#         # remove client
#         del room["clients"][client_id]
#         del room["cards"][client_id]

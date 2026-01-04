import asyncio
import json
import websockets

SERVER_URL = "wss://YOUR-TUNNEL-URL/ws"
SERVER_URL = "ws://127.0.0.1:8000/ws"
ROOM_ID = "room1"


class BingoClient:
    def __init__(self):
        self.card = []
        self.marked = set()
        self.client_id = None

    def display_card(self):
        print("\nYour Bingo Card:")
        for i, option in enumerate(self.card, start=1):
            status = "✔" if option in self.marked else " "
            print(f"[{status}] {i:2d}. {option}")

    async def handle_server_message(self, message: dict):
        msg_type = message["type"]

        if msg_type == "init":
            self.client_id = message["client_id"]
            self.card = message["card"]
            self.marked = set(message["marked"])

            print(f"\nConnected! Client ID: {self.client_id}")
            self.display_card()

        elif msg_type == "update":
            option = message["option"]
            action = message["action"]

            if option in self.card:
                if action == "mark":
                    self.marked.add(option)
                elif action == "unmark":
                    self.marked.discard(option)

                print(f"\nUpdate from room: {action.upper()} '{option}'")
                self.display_card()

    async def user_input_loop(self, ws):
        loop = asyncio.get_event_loop()

        while True:
            user_input = await loop.run_in_executor(
                None, input, "\nEnter number to toggle (1–24), or 'q' to quit: "
            )

            if user_input.lower() == "q":
                break

            try:
                index = int(user_input) - 1
                if index < 0 or index >= len(self.card):
                    raise ValueError

                option = self.card[index]

                if option in self.marked:
                    await ws.send(json.dumps({
                        "type": "unmark",
                        "option": option,
                    }))
                else:
                    await ws.send(json.dumps({
                        "type": "mark",
                        "option": option,
                    }))

            except ValueError:
                print("Invalid input")

    async def run(self):
        url = f"{SERVER_URL}/{ROOM_ID}"

        async with websockets.connect(url) as ws:
            receiver = asyncio.create_task(self.receive_loop(ws))
            sender = asyncio.create_task(self.user_input_loop(ws))

            done, pending = await asyncio.wait(
                [receiver, sender],
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in pending:
                task.cancel()

    async def receive_loop(self, ws):
        async for message in ws:
            await self.handle_server_message(json.loads(message))


if __name__ == "__main__":
    asyncio.run(BingoClient().run())

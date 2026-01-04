import sys
import json
import websockets
import asyncio
import threading
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton,
    QGridLayout, QVBoxLayout, QMessageBox,
    QLabel, QInputDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QIcon


# ===================== CONFIG =====================
SERVER_URL = "ws://127.0.0.1:8000/ws"   # or wss://your-cloudflare-url/ws
SERVER_URL = "wss://consensus-terrorists-recorded-static.trycloudflare.com/ws"
CARD_SIZE = 24
# =================================================


def resource_path(relative_path):
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return base_path / relative_path


# ---------- Qt → WebSocket bridge ----------
class BingoSignals(QObject):
    init_card = pyqtSignal(list, list)   # card, marked
    update = pyqtSignal(str, str)        # action, option


class BingoWSClient:
    def __init__(self, signals, server_url: str, room_id: str):
        self.signals = signals
        self.server_url = f"{server_url.replace("https", "wss")}/ws"
        self.room_id = room_id
        self.ws = None
        self.loop = None

    async def run(self):
        self.loop = asyncio.get_running_loop()
        url = f"{self.server_url}/{self.room_id}"

        async with websockets.connect(url) as ws:
            self.ws = ws
            async for message in ws:
                data = json.loads(message)

                if data["type"] == "init":
                    self.signals.init_card.emit(
                        data["card"],
                        data["marked"]
                    )

                elif data["type"] == "update":
                    self.signals.update.emit(
                        data["action"],
                        data["option"]
                    )

    def send(self, payload: dict):
        asyncio.run_coroutine_threadsafe(
            self.ws.send(json.dumps(payload)),
            self.loop
        )


# ---------- Main UI ----------
class BingoGrid(QWidget):
    def __init__(self):
        super().__init__()

        self.server_url = self.prompt_for_url()
        self.room_id = self.prompt_for_room()  # 👈 NEW

        self.setWindowTitle(f"Multiplayer Bingo — Room: {self.room_id}")
        self.resize(520, 520)
        self.setWindowIcon(QIcon(str(resource_path("resources/icons/icon.ico"))))

        self.layout = QVBoxLayout(self)
        self.info = QLabel("Connecting to bingo room...")
        self.info.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.info)

        self.grid = QGridLayout()
        self.layout.addLayout(self.grid)

        self.buttons = {}
        self.ws_client = None

        self.signals = BingoSignals()
        self.signals.init_card.connect(self.build_grid)
        self.signals.update.connect(self.apply_remote_update)

        self.start_ws_thread()

    def prompt_for_url(self) -> str:
        while True:
            url, ok = QInputDialog.getText(
                self,
                "Provide host url",
                "Enter host url:",
            )

            if not ok or not url.strip():
                QMessageBox.information(
                    self,
                    "No URL",
                    "You must enter a url to continue."
                )
                continue

            return url.strip()
        sys.exit(0)

    def prompt_for_room(self) -> str:
        while True:
            room, ok = QInputDialog.getText(
                self,
                "Join Bingo Room",
                "Enter room name:",
            )

            if not ok or not room.strip():
                QMessageBox.information(
                    self,
                    "No Room",
                    "You must enter a room name to continue."
                )
                continue

            return room.strip()
        sys.exit(0)

    # ---------- WebSocket thread ----------
    def start_ws_thread(self):
        def runner():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.ws_client = BingoWSClient(
                self.signals,
                self.server_url,
                self.room_id,
            )
            loop.run_until_complete(self.ws_client.run())

        threading.Thread(target=runner, daemon=True).start()

    # ---------- UI ----------
    def build_grid(self, card, marked):
        self.info.setText("Connected — Bingo in progress")

        index = 0
        for row in range(5):
            for col in range(5):

                if row == 2 and col == 2:
                    btn = self.create_button("FREE")
                    btn.setStyleSheet("background-color: lightgreen; font-weight: bold;")
                    btn.marked = True
                    self.grid.addWidget(btn, row, col)
                    continue

                text = card[index]
                index += 1

                btn = self.create_button(text)
                self.grid.addWidget(btn, row, col)
                self.buttons[text] = btn

                if text in marked:
                    self.set_mark(btn, True)

    def create_button(self, text):
        btn = QPushButton(text)
        btn.setFixedSize(100, 60)
        btn.original_text = text
        btn.marked = False

        btn.clicked.connect(lambda _, b=btn: self.toggle_mark(b))
        return btn

    # ---------- Mark handling ----------
    def toggle_mark(self, button):
        new_state = not button.marked
        self.set_mark(button, new_state)

        self.ws_client.send({
            "action": "mark" if new_state else "unmark",
            "option": button.original_text
        })

    def set_mark(self, button, state: bool):
        button.marked = state
        if state:
            button.setText(f"{button.original_text}\n❌")
        else:
            button.setText(button.original_text)

    # ---------- Remote updates ----------
    def apply_remote_update(self, action, option):
        if option not in self.buttons:
            return

        btn = self.buttons[option]
        self.set_mark(btn, action == "mark")


# ---------- Run ----------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BingoGrid()
    window.show()
    sys.exit(app.exec_())

import sys
from pathlib import Path
import random
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton,
    QGridLayout, QFileDialog, QVBoxLayout, QMessageBox, QLabel
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller"""
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return base_path / relative_path

class BingoGrid(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Custom Bingo Grid - 5x5")
        self.resize(500, 500)
        self.setWindowIcon(QIcon(str(resource_path("resources/icons/icon.ico"))))

        layout = QVBoxLayout()
        self.setLayout(layout)

        info = QLabel("Select a text file with at least 24 items (one per line)")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)

        self.grid = QGridLayout()
        layout.addLayout(self.grid)

        self.buttons = []
        self.load_items_and_build_grid()

    def load_items_and_build_grid(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Text File With Bingo Items",
            "",
            "Text Files (*.txt)"
        )

        if not path:
            QMessageBox.warning(self, "No File", "You must select a valid .txt file")
            return

        with open(path, "r", encoding="utf-8") as f:
            items = [line.strip() for line in f if line.strip()]

        if len(items) < 24:
            QMessageBox.critical(self, "Not Enough Items",
                                 f"File must contain at least 24 items.\nFound only {len(items)}.")
            return

        chosen = random.sample(items, 24)

        index = 0
        for row in range(5):
            row_buttons = []
            for col in range(5):

                if row == 2 and col == 2:
                    # FREE center
                    btn = self.create_button("FREE")
                    btn.setStyleSheet("background-color: lightgreen; font-weight: bold;")
                    self.grid.addWidget(btn, row, col)
                    row_buttons.append(btn)
                    continue

                text = chosen[index]
                index += 1

                btn = self.create_button(text)
                self.grid.addWidget(btn, row, col)
                row_buttons.append(btn)

            self.buttons.append(row_buttons)

    def create_button(self, text):
        btn = QPushButton(text)
        btn.setFixedSize(100, 60)

        # Store original label
        btn.original_text = text
        btn.marked = False  # not clicked yet

        btn.clicked.connect(lambda checked, b=btn: self.toggle_mark(b))
        return btn

    def toggle_mark(self, button):
        if button.marked:
            # Remove X
            button.setText(button.original_text)
            button.marked = False
            
        else:
            # Add X (❌ is large and centered)
            button.setText(f"{button.original_text}\n❌")
            button.marked = True


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BingoGrid()
    window.show()
    sys.exit(app.exec_())

from pathlib import Path
import psycopg2

TXT_FILE = Path("../options.txt")

DB_CONFIG = {
    "host": "127.0.0.1",
    "dbname": "bingo",
    "user": "bingo",
    "password": "bingo",
    "port": 5432,
}

def insert_options(txt_path: Path) -> None:
    values = []

    with txt_path.open("r", encoding="utf-8") as f:
        for line in f:
            text = line.strip()
            if text:  # skip empty lines
                values.append((text,))

    if not values:
        return

    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO options (text)
                    VALUES (%s)
                    ON CONFLICT (text) DO NOTHING
                    """,
                    values,
                )
    finally:
        conn.close()

if __name__ == "__main__":
    insert_options(TXT_FILE)

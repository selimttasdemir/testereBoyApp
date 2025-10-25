import sqlite3
from datetime import datetime


def init_db(db_path: str):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            boy REAL NOT NULL,
            tampon TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def add_record(db_path: str, boy: float, tampon: str):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    cur.execute("INSERT INTO records (boy, tampon, created_at) VALUES (?, ?, ?)", (boy, tampon, now))
    conn.commit()
    conn.close()


def get_records(db_path: str):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Order ASC so newer records appear at the bottom of the list
    cur.execute("SELECT id, boy, tampon, created_at FROM records ORDER BY created_at ASC")
    rows = cur.fetchall()
    conn.close()
    return rows


def update_record(db_path: str, record_id: int, boy: float, tampon: str):
    """Update boy and tampon for an existing record. Does not change created_at."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("UPDATE records SET boy = ?, tampon = ? WHERE id = ?", (boy, tampon, record_id))
    conn.commit()
    conn.close()


def delete_record(db_path: str, record_id: int):
    """Delete a record from the database."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("DELETE FROM records WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()

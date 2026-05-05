import sqlite3

DB_PATH = "users.db"

def get_db():
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    return con
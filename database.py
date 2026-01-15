import sqlite3

DB_NAME = "approval_system.db"

def get_connection():
    """Creates and returns a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(DB_NAME)
        return conn
    except sqlite3.Error as e:
        print(f"Connection error: {e}")
        return None
import sqlite3
import json


class SQLiteEventStore:
    def __init__(self, db_path="mypixler_events.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False, timeout=5)
        self._init()

    def _init(self):
        cur = self.conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_name TEXT,
            timestamp REAL,
            state TEXT,
            project_name TEXT,
            metadata TEXT
        )
        """)
        self.conn.commit()

    def append(self, event):
        cur = self.conn.cursor()
        cur.execute("""
        INSERT INTO events VALUES (NULL, ?, ?, ?, ?, ?)
        """, (
            event["event"],
            event["timestamp"],
            event["state"],
            event.get("project_name"),
            json.dumps(event.get("metadata", {}))
        ))
        self.conn.commit()
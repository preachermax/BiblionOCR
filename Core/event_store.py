import sqlite3
import json

from .event_bus import normalize_event


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
        event = normalize_event(event)
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

    def list_events(
        self,
        project_name=None,
        event_name=None,
        state=None,
        since_timestamp=None,
        until_timestamp=None,
        limit=None,
        offset=0,
        ascending=True,
    ):
        """Return normalized events using optional filters and deterministic ordering."""
        query = (
            "SELECT event_name, timestamp, state, project_name, metadata "
            "FROM events"
        )
        filters = []
        params = []

        if project_name is not None:
            filters.append("project_name = ?")
            params.append(project_name)
        if event_name is not None:
            filters.append("event_name = ?")
            params.append(event_name)
        if state is not None:
            filters.append("state = ?")
            params.append(state)
        if since_timestamp is not None:
            filters.append("timestamp >= ?")
            params.append(float(since_timestamp))
        if until_timestamp is not None:
            filters.append("timestamp <= ?")
            params.append(float(until_timestamp))

        if filters:
            query += " WHERE " + " AND ".join(filters)

        order = "ASC" if ascending else "DESC"
        query += f" ORDER BY id {order}"

        if limit is not None:
            query += " LIMIT ?"
            params.append(int(limit))
            if offset:
                query += " OFFSET ?"
                params.append(int(offset))
        elif offset:
            query += " LIMIT -1 OFFSET ?"
            params.append(int(offset))

        cur = self.conn.cursor()
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        return [self._row_to_event(row) for row in rows]

    def replay(self, project_name=None):
        """Replay event stream in append order."""
        return self.list_events(project_name=project_name, ascending=True)

    def reconstruct_project_state(self, project_name=None):
        """Build a coarse state snapshot from replayed events."""
        state = {
            "validated": False,
            "provenance_captured": False,
            "ris_generated": False,
            "structure_created": False,
            "filesystem_written": False,
            "project_registered": False,
            "project_created": False,
            "failed": False,
            "last_state": None,
            "event_count": 0,
        }

        for event in self.replay(project_name=project_name):
            name = event["event"]
            state["last_state"] = event.get("state")
            state["event_count"] += 1

            if name == "validation_passed":
                state["validated"] = True
            elif name == "provenance_captured":
                state["provenance_captured"] = True
            elif name == "ris_generated":
                state["ris_generated"] = True
            elif name == "project_structure_created":
                state["structure_created"] = True
            elif name == "filesystem_written":
                state["filesystem_written"] = True
            elif name == "project_registered":
                state["project_registered"] = True
            elif name == "project_created":
                state["project_created"] = True
            elif name == "project_failed":
                state["failed"] = True

        return state

    def close(self):
        self.conn.close()

    @staticmethod
    def _row_to_event(row):
        event_name, timestamp, state, project_name, metadata_blob = row
        try:
            metadata = json.loads(metadata_blob) if metadata_blob else {}
        except json.JSONDecodeError:
            metadata = {"raw": metadata_blob}

        return normalize_event({
            "event": event_name,
            "timestamp": timestamp,
            "state": state,
            "project_name": project_name,
            "metadata": metadata,
        })
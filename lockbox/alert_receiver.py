"""Accept an alert once, even when the sender retries after a receiver restart."""
import json
from pathlib import Path
import sqlite3


class AlertReceiver:
    def __init__(self, path=None):
        if path:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path or ':memory:', timeout=0.1)
        try:
            self.connection.execute('PRAGMA synchronous = FULL')
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS receipts (
                    session TEXT NOT NULL,
                    event_id INTEGER NOT NULL,
                    event_json TEXT NOT NULL,
                    PRIMARY KEY (session, event_id)
                )
            """)
        except sqlite3.Error:
            self.close()
            raise

    def close(self):
        self.connection.close()

    def record(self, event):
        if not isinstance(event, dict):
            raise ValueError('Alert must be an object')
        session, event_id = event.get('session'), event.get('id')
        if not isinstance(session, str) or not session or type(event_id) is not int or not 0 < event_id < 2**63:
            raise ValueError('Invalid alert identity')

        # The receipt row is the simulated notification. The caller may ACK
        # only after this transaction commits, including when the row exists.
        with self.connection:
            result = self.connection.execute("""
                INSERT INTO receipts (session, event_id, event_json) VALUES (?, ?, ?)
                ON CONFLICT (session, event_id) DO NOTHING
            """, (session, event_id, json.dumps(event, allow_nan=False)))
        return result.rowcount == 1

    def sessions(self):
        sessions = {}
        for session, event_id in self.connection.execute(
            'SELECT session, event_id FROM receipts ORDER BY rowid'
        ):
            sessions.setdefault(session, []).append(event_id)
        return sessions

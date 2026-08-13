"""
Activity log storage. SQLite is a local file — same problem as local disk
for uploads: it won't persist reliably across Vercel serverless invocations.

- If DATABASE_URL is set (e.g. the Neon Postgres integration on Vercel),
  logs go to Postgres.
- Otherwise (local dev), logs go to a local SQLite file, same as the
  original app.

If neither is reachable, logging fails silently — activity logging is a
nice-to-have, not something that should break the core CSV -> deck flow.
"""

import os
import sqlite3
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL")
SQLITE_PATH = "activity_log.db"

_pg_pool = None
if DATABASE_URL:
    import psycopg2
    import psycopg2.pool
    _pg_pool = psycopg2.pool.SimpleConnectionPool(1, 5, DATABASE_URL)


def _get_pg_conn():
    return _pg_pool.getconn()


def _put_pg_conn(conn):
    _pg_pool.putconn(conn)


def init_db():
    try:
        if DATABASE_URL:
            conn = _get_pg_conn()
            try:
                c = conn.cursor()
                c.execute('''CREATE TABLE IF NOT EXISTS logins (
                                id SERIAL PRIMARY KEY,
                                "user" TEXT,
                                timestamp TEXT,
                                action TEXT
                            )''')
                c.execute('''CREATE TABLE IF NOT EXISTS generations (
                                id SERIAL PRIMARY KEY,
                                "user" TEXT,
                                timestamp TEXT,
                                source_file TEXT,
                                report_file TEXT,
                                theme TEXT
                            )''')
                conn.commit()
            finally:
                _put_pg_conn(conn)
        else:
            conn = sqlite3.connect(SQLITE_PATH)
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS logins (
                            id INTEGER PRIMARY KEY,
                            user TEXT,
                            timestamp TEXT,
                            action TEXT
                        )''')
            c.execute('''CREATE TABLE IF NOT EXISTS generations (
                            id INTEGER PRIMARY KEY,
                            user TEXT,
                            timestamp TEXT,
                            source_file TEXT,
                            report_file TEXT,
                            theme TEXT
                        )''')
            conn.commit()
            conn.close()
    except Exception as e:
        print("DB init skipped:", e)


def log_activity(user, action, details=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        if DATABASE_URL:
            conn = _get_pg_conn()
            try:
                c = conn.cursor()
                if action == "login":
                    c.execute(
                        'INSERT INTO logins ("user", timestamp, action) VALUES (%s, %s, %s)',
                        (user, timestamp, action),
                    )
                elif action == "generate_ppt":
                    c.execute(
                        'INSERT INTO generations ("user", timestamp, source_file, report_file, theme) '
                        'VALUES (%s, %s, %s, %s, %s)',
                        (user, timestamp, details["source_file"], details["report_file"], details["theme"]),
                    )
                conn.commit()
            finally:
                _put_pg_conn(conn)
        else:
            conn = sqlite3.connect(SQLITE_PATH)
            c = conn.cursor()
            if action == "login":
                c.execute(
                    "INSERT INTO logins (user, timestamp, action) VALUES (?, ?, ?)",
                    (user, timestamp, action),
                )
            elif action == "generate_ppt":
                c.execute(
                    "INSERT INTO generations (user, timestamp, source_file, report_file, theme) VALUES (?, ?, ?, ?, ?)",
                    (user, timestamp, details["source_file"], details["report_file"], details["theme"]),
                )
            conn.commit()
            conn.close()
    except Exception as e:
        # Activity logging is best-effort; never break the user's flow over it.
        print("log_activity failed:", e)


def fetch_logs():
    """Returns (logins, generations) as lists of tuples, newest first."""
    try:
        if DATABASE_URL:
            conn = _get_pg_conn()
            try:
                c = conn.cursor()
                c.execute("SELECT * FROM logins ORDER BY timestamp DESC")
                logins = c.fetchall()
                c.execute("SELECT * FROM generations ORDER BY timestamp DESC")
                generations = c.fetchall()
                return logins, generations
            finally:
                _put_pg_conn(conn)
        else:
            conn = sqlite3.connect(SQLITE_PATH)
            c = conn.cursor()
            c.execute("SELECT * FROM logins ORDER BY timestamp DESC")
            logins = c.fetchall()
            c.execute("SELECT * FROM generations ORDER BY timestamp DESC")
            generations = c.fetchall()
            conn.close()
            return logins, generations
    except Exception as e:
        print("fetch_logs failed:", e)
        return [], []

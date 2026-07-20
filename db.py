import sqlite3
from pathlib import Path
from datetime import datetime, date, timedelta

DB_PATH = Path(__file__).parent / "unwind.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    with open(SCHEMA_PATH) as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


# ---------------- Notes ----------------

def create_note(title, content="", tags=""):
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO notes (title, content, tags) VALUES (?, ?, ?)",
        (title, content, tags),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def update_note(note_id, title, content, tags):
    conn = get_connection()
    conn.execute(
        "UPDATE notes SET title = ?, content = ?, tags = ?, updated_at = datetime('now') WHERE id = ?",
        (title, content, tags, note_id),
    )
    conn.commit()
    conn.close()


def delete_note(note_id):
    conn = get_connection()
    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()


def get_note(note_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def list_notes(tag=None):
    conn = get_connection()
    if tag:
        # tags stored comma-separated; match tag as a whole token, not substring
        rows = conn.execute(
            "SELECT * FROM notes WHERE (',' || tags || ',') LIKE ? ORDER BY updated_at DESC",
            (f"%,{tag},%",),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM notes ORDER BY updated_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_notes(query):
    """Real full-text search via SQLite FTS5 -- matches whole words/phrases
    across title, content, and tags, ranked by relevance."""
    if not query or not query.strip():
        return list_notes()

    conn = get_connection()
    # FTS5 query syntax needs simple terms; sanitize by quoting each word so
    # punctuation in user input doesn't break the query syntax.
    terms = query.strip().split()
    safe_query = " ".join(f'"{t}"' for t in terms)

    try:
        rows = conn.execute(
            """SELECT notes.* FROM notes
               JOIN notes_fts ON notes.id = notes_fts.rowid
               WHERE notes_fts MATCH ?
               ORDER BY rank""",
            (safe_query,),
        ).fetchall()
    except sqlite3.OperationalError:
        # Malformed FTS query (rare edge case) -- fall back to a plain scan.
        rows = conn.execute(
            "SELECT * FROM notes WHERE title LIKE ? OR content LIKE ? ORDER BY updated_at DESC",
            (f"%{query}%", f"%{query}%"),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def all_tags():
    conn = get_connection()
    rows = conn.execute("SELECT tags FROM notes WHERE tags != ''").fetchall()
    conn.close()
    tag_set = set()
    for r in rows:
        for t in r["tags"].split(","):
            t = t.strip()
            if t:
                tag_set.add(t)
    return sorted(tag_set)


# ---------------- Timer ----------------

def log_session(subject, duration_seconds, started_at, ended_at):
    conn = get_connection()
    conn.execute(
        "INSERT INTO timer_sessions (subject, duration_seconds, started_at, ended_at) VALUES (?, ?, ?, ?)",
        (subject, duration_seconds, started_at, ended_at),
    )
    conn.commit()
    conn.close()


def recent_sessions(limit=20):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM timer_sessions ORDER BY started_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def timer_stats():
    conn = get_connection()

    today_str = date.today().isoformat()
    today_seconds = conn.execute(
        "SELECT COALESCE(SUM(duration_seconds), 0) as s FROM timer_sessions WHERE date(started_at) = ?",
        (today_str,),
    ).fetchone()["s"]

    total_seconds = conn.execute(
        "SELECT COALESCE(SUM(duration_seconds), 0) as s FROM timer_sessions"
    ).fetchone()["s"]

    by_subject = conn.execute(
        """SELECT subject, SUM(duration_seconds) as total FROM timer_sessions
           WHERE subject != '' GROUP BY subject ORDER BY total DESC"""
    ).fetchall()

    # Streak: consecutive days (including today) with at least one session.
    day_rows = conn.execute(
        "SELECT DISTINCT date(started_at) as d FROM timer_sessions ORDER BY d DESC"
    ).fetchall()
    conn.close()

    streak = 0
    expected = date.today()
    day_set = {row["d"] for row in day_rows}
    while expected.isoformat() in day_set:
        streak += 1
        expected -= timedelta(days=1)

    return {
        "today_seconds": today_seconds,
        "total_seconds": total_seconds,
        "by_subject": [dict(r) for r in by_subject],
        "streak": streak,
    }


def week_activity():
    """
    Which days of the current week (Mon-Sun) have at least one logged
    session -- real data, used for the weekly streak strip in the UI.
    Returns a list of 7 dicts: [{'label': 'M', 'date': '2026-07-20', 'active': True}, ...]
    """
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT date(started_at) as d FROM timer_sessions "
        "WHERE date(started_at) >= ? AND date(started_at) <= ?",
        (monday.isoformat(), (monday + timedelta(days=6)).isoformat()),
    ).fetchall()
    conn.close()
    active_days = {r["d"] for r in rows}

    labels = ["M", "T", "W", "T", "F", "S", "S"]
    result = []
    for i in range(7):
        d = monday + timedelta(days=i)
        result.append({
            "label": labels[i],
            "date": d.isoformat(),
            "active": d.isoformat() in active_days,
            "is_today": d == today,
        })
    return result


def count_notes():
    conn = get_connection()
    n = conn.execute("SELECT COUNT(*) as c FROM notes").fetchone()["c"]
    conn.close()
    return n


def count_sessions_this_week():
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    conn = get_connection()
    n = conn.execute(
        "SELECT COUNT(*) as c FROM timer_sessions WHERE date(started_at) >= ?",
        (monday.isoformat(),),
    ).fetchone()["c"]
    conn.close()
    return n


def get_setting(key, default=None):
    conn = get_connection()
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key, value):
    conn = get_connection()
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()
    conn.close()

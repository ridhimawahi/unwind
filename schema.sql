CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL DEFAULT '',
    tags TEXT NOT NULL DEFAULT '',   -- comma-separated, kept simple for v1
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Real full-text search index over notes, kept in sync via triggers below.
-- This is what makes search actually good (matches whole words/phrases
-- across title+content+tags) instead of a slow, dumb LIKE '%term%' scan.
CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
    title, content, tags, content='notes', content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS notes_ai AFTER INSERT ON notes BEGIN
    INSERT INTO notes_fts(rowid, title, content, tags) VALUES (new.id, new.title, new.content, new.tags);
END;

CREATE TRIGGER IF NOT EXISTS notes_ad AFTER DELETE ON notes BEGIN
    INSERT INTO notes_fts(notes_fts, rowid, title, content, tags) VALUES ('delete', old.id, old.title, old.content, old.tags);
END;

CREATE TRIGGER IF NOT EXISTS notes_au AFTER UPDATE ON notes BEGIN
    INSERT INTO notes_fts(notes_fts, rowid, title, content, tags) VALUES ('delete', old.id, old.title, old.content, old.tags);
    INSERT INTO notes_fts(rowid, title, content, tags) VALUES (new.id, new.title, new.content, new.tags);
END;

CREATE TABLE IF NOT EXISTS timer_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT NOT NULL DEFAULT '',
    duration_seconds INTEGER NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_timer_started ON timer_sessions(started_at);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

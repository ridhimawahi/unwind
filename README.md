# Unwind

A calm, all in one study space — notes, focus timer, and (coming soon)
quizzes and book recommendations, all in one place instead of five
different apps.

## Status: Phase 1 of 3

This is being built in phases so each part is fully working and testable
before the next one starts, rather than one big risky build.

- ✅ **Phase 1 (this version):** Notes with real full-text search, and a
  study timer with stats/streaks. Fully self-contained — no accounts, no
  API keys, no external services. Works the moment you run it.
- ⏳ **Phase 2 (next):** Book Finder — searches a free, public book API
  for books matching your note topics. No login/key needed for this one.
- ⏳ **Phase 3:** Quizzes generated from your notes.

## Why this setup is genuinely zero-friction

Unlike an earlier version of this project, Phase 1 has **no external
accounts, tokens, or API keys of any kind.** Just Python + a local
database. Clone it, install, run — that's the whole setup.

## Tech stack

- Python / Flask
- SQLite, using its built-in **FTS5 full-text search** for notes (real
  word/phrase search, not just a slow text scan — no extra library needed)
- Vanilla HTML/CSS/JS (the timer is plain JavaScript, no framework)

## Setup

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## Features in this version

**Design**
- Sidebar navigation matching the reference design, with future features
  (Quizzes, Flashcards, Study Sets, Calendar, Progress, Bookmarks) visible
  but greyed out — so the app already looks and feels like the full
  planned product, not just a fragment
- Working dark mode toggle (top right) — persists across visits
- Everything shown on the dashboard is real data — no placeholder/fake
  numbers. Sections that need features we haven't built yet (like quiz
  progress) are marked "coming soon" rather than faked

**Notes**
- Create, edit, delete, tag notes
- Real full-text search (try searching for a word that's only in the body
  of a note, not the title — it'll still find it)
- Filter by tag, with consistent color-coding per tag

**Timer**
- Start / pause / stop a study session, tagged with a subject
- Sessions are logged automatically on stop (anything under 5 seconds is
  ignored as accidental)
- Dashboard shows today's total, current streak, weekly activity strip,
  and time-per-subject — all computed live from your actual sessions

**Settings**
- Set your display name, used in the dashboard greeting

## Project structure

```
unwind/
├── app.py          # Flask routes
├── db.py           # notes (with FTS5 search), timer, settings storage
├── schema.sql
├── templates/
│   ├── base.html          # sidebar shell shared across all pages
│   ├── icons.html          # icon set (outline-style, matches design)
│   ├── dashboard.html
│   ├── notes.html          # list + search
│   ├── note_form.html      # create/edit (shared)
│   ├── note_view.html
│   ├── timer.html
│   └── settings.html
└── static/style.css        # pastel design system + dark mode
```

**Note on styling:** now matches the provided visual reference (pastel
palette, sidebar nav, illustrated cards). Colors/spacing can still be
refined further once you've seen it running.

## Roadmap

- [ ] Phase 2: Book Finder (public API, no key needed)
- [ ] Phase 3: AI-generated quizzes from notes (needs one API key — see
  discussion before starting this phase)
- [ ] Final visual design pass

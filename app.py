from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import db

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-if-deploying"


@app.before_request
def ensure_db():
    if not db.DB_PATH.exists():
        db.init_db()


def format_duration(seconds):
    """e.g. 3725 -> '1h 2m'. Kept here (not in db.py) since it's purely display logic."""
    seconds = int(seconds or 0)
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    return f"{minutes}m"


app.jinja_env.filters["duration"] = format_duration

TAG_COLORS = ["purple", "peach", "mint", "gold", "blue"]


def tag_color(tag):
    if not tag:
        return "purple"
    h = sum(ord(c) for c in tag.lower())
    return TAG_COLORS[h % len(TAG_COLORS)]


app.jinja_env.globals["tag_color"] = tag_color

DAILY_GOAL_SECONDS = 2 * 60 * 60  # 2 hours -- used only for the promo card's progress bar

ACTIVE_PAGE_BY_ENDPOINT = {
    "dashboard": "home",
    "notes_list": "notes", "notes_new": "notes", "notes_view": "notes", "notes_edit": "notes",
    "timer_page": "timer",
}


@app.context_processor
def inject_globals():
    stats = db.timer_stats()
    goal_pct = min(int(stats["today_seconds"] / DAILY_GOAL_SECONDS * 100), 100)
    return {
        "display_name": db.get_setting("display_name") or "there",
        "today_goal_pct": goal_pct,
        "active_page": ACTIVE_PAGE_BY_ENDPOINT.get(request.endpoint),
    }


def time_of_day_greeting():
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning"
    if hour < 18:
        return "Good afternoon"
    return "Good evening"


@app.route("/")
def dashboard():
    notes = db.list_notes()[:4]
    stats = db.timer_stats()
    recent = db.recent_sessions(limit=4)
    week = db.week_activity()
    return render_template(
        "dashboard.html",
        notes=notes,
        stats=stats,
        recent=recent,
        week=week,
        greeting=time_of_day_greeting(),
        note_count=db.count_notes(),
        sessions_this_week=db.count_sessions_this_week(),
    )


# ---------------- Notes ----------------

@app.route("/notes")
def notes_list():
    query = request.args.get("q", "").strip()
    tag = request.args.get("tag") or None

    if query:
        notes = db.search_notes(query)
    else:
        notes = db.list_notes(tag=tag)

    return render_template(
        "notes.html", notes=notes, query=query, active_tag=tag, tags=db.all_tags()
    )


@app.route("/notes/new", methods=["GET", "POST"])
def notes_new():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        tags = request.form.get("tags", "").strip()
        if not title:
            flash("Title is required.")
            return redirect(url_for("notes_new"))
        note_id = db.create_note(title, content, tags)
        return redirect(url_for("notes_view", note_id=note_id))

    return render_template("note_form.html", note=None)


@app.route("/notes/<int:note_id>")
def notes_view(note_id):
    note = db.get_note(note_id)
    if not note:
        flash("Note not found.")
        return redirect(url_for("notes_list"))
    return render_template("note_view.html", note=note)


@app.route("/notes/<int:note_id>/edit", methods=["GET", "POST"])
def notes_edit(note_id):
    note = db.get_note(note_id)
    if not note:
        flash("Note not found.")
        return redirect(url_for("notes_list"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        tags = request.form.get("tags", "").strip()
        if not title:
            flash("Title is required.")
            return redirect(url_for("notes_edit", note_id=note_id))
        db.update_note(note_id, title, content, tags)
        return redirect(url_for("notes_view", note_id=note_id))

    return render_template("note_form.html", note=note)


@app.route("/notes/<int:note_id>/delete", methods=["POST"])
def notes_delete(note_id):
    db.delete_note(note_id)
    flash("Note deleted.")
    return redirect(url_for("notes_list"))


# ---------------- Timer ----------------

@app.route("/timer")
def timer_page():
    stats = db.timer_stats()
    recent = db.recent_sessions(limit=10)
    return render_template("timer.html", stats=stats, recent=recent)


@app.route("/timer/log", methods=["POST"])
def timer_log():
    subject = request.form.get("subject", "").strip() or "General"
    duration_seconds = request.form.get("duration_seconds", "0")
    started_at = request.form.get("started_at", "")
    try:
        duration_seconds = int(float(duration_seconds))
    except ValueError:
        duration_seconds = 0

    if duration_seconds < 5:
        # Ignore accidental near-instant starts/stops -- not worth logging.
        return redirect(url_for("timer_page"))

    try:
        started_dt = datetime.fromisoformat(started_at)
    except (ValueError, TypeError):
        started_dt = datetime.now()

    ended_dt = datetime.now()
    db.log_session(subject, duration_seconds, started_dt.isoformat(), ended_dt.isoformat())
    flash(f"Logged {format_duration(duration_seconds)} of {subject}.")
    return redirect(url_for("timer_page"))


# ---------------- Settings ----------------

@app.route("/settings", methods=["GET", "POST"])
def settings_page():
    if request.method == "POST":
        name = request.form.get("display_name", "").strip()
        db.set_setting("display_name", name)
        flash("Settings saved.")
        return redirect(url_for("settings_page"))

    return render_template("settings.html", current_name=db.get_setting("display_name") or "")


if __name__ == "__main__":
    db.init_db()
    app.run(debug=True, port=5000)

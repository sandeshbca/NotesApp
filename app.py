import os
import sqlite3
from datetime import datetime
from functools import wraps

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "change-this-secret-key-before-production"),
    DATABASE=os.path.join(app.root_path, "notes.db"),
)


def get_db():
    """Return the request-scoped SQLite connection."""
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL DEFAULT '',
            color TEXT NOT NULL DEFAULT 'violet',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        """
    )
    db.commit()


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to open your notes.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def current_user():
    if "user_id" not in session:
        return None
    return get_db().execute(
        "SELECT id, name, email FROM users WHERE id = ?", (session["user_id"],)
    ).fetchone()


def get_owned_note(note_id):
    return get_db().execute(
        "SELECT * FROM notes WHERE id = ? AND user_id = ?",
        (note_id, session["user_id"]),
    ).fetchone()


@app.context_processor
def inject_current_user():
    return {"current_user": current_user()}


@app.template_filter("friendly_date")
def friendly_date(value):
    try:
        return datetime.fromisoformat(value).strftime("%d %b %Y · %I:%M %p")
    except (TypeError, ValueError):
        return value


@app.get("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("home.html")


@app.route("/register", methods=("GET", "POST"))
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        error = None
        if len(name) < 2:
            error = "Please enter your name (at least 2 characters)."
        elif "@" not in email or "." not in email.rsplit("@", 1)[-1]:
            error = "Enter a valid email address."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        elif password != confirm_password:
            error = "Passwords do not match."
        if error is None:
            try:
                db = get_db()
                db.execute(
                    "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                    (name, email, generate_password_hash(password), datetime.now().isoformat()),
                )
                db.commit()
                flash("Account created. You can sign in now.", "success")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                error = "An account with that email already exists."
        flash(error, "error")
    return render_template("register.html")


@app.route("/login", methods=("GET", "POST"))
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Incorrect email or password.", "error")
        else:
            session.clear()
            session["user_id"] = user["id"]
            flash(f"Welcome back, {user['name'].split()[0]}!", "success")
            return redirect(url_for("dashboard"))
    return render_template("login.html")


@app.post("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("login"))


@app.get("/dashboard")
@login_required
def dashboard():
    notes = get_db().execute(
        "SELECT * FROM notes WHERE user_id = ? ORDER BY updated_at DESC", (session["user_id"],)
    ).fetchall()
    return render_template("dashboard.html", notes=notes, total_notes=len(notes))


@app.route("/notes/new", methods=("GET", "POST"))
@login_required
def create_note():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        color = request.form.get("color", "violet")
        if not title:
            flash("A note title is required.", "error")
        else:
            now = datetime.now().isoformat()
            get_db().execute(
                "INSERT INTO notes (user_id, title, content, color, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (session["user_id"], title, content, color if color in COLORS else "violet", now, now),
            )
            get_db().commit()
            flash("Your note has been created.", "success")
            return redirect(url_for("dashboard"))
    return render_template("note_form.html", note=None, page_title="Create a note")


@app.route("/notes/<int:note_id>/edit", methods=("GET", "POST"))
@login_required
def edit_note(note_id):
    note = get_owned_note(note_id)
    if note is None:
        flash("Note not found.", "error")
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        color = request.form.get("color", "violet")
        if not title:
            flash("A note title is required.", "error")
        else:
            get_db().execute(
                "UPDATE notes SET title = ?, content = ?, color = ?, updated_at = ? WHERE id = ? AND user_id = ?",
                (title, content, color if color in COLORS else "violet", datetime.now().isoformat(), note_id, session["user_id"]),
            )
            get_db().commit()
            flash("Changes saved.", "success")
            return redirect(url_for("dashboard"))
    return render_template("note_form.html", note=note, page_title="Edit note")


@app.post("/notes/<int:note_id>/delete")
@login_required
def delete_note(note_id):
    if get_owned_note(note_id) is None:
        flash("Note not found.", "error")
    else:
        get_db().execute("DELETE FROM notes WHERE id = ? AND user_id = ?", (note_id, session["user_id"]))
        get_db().commit()
        flash("Note deleted.", "success")
    return redirect(url_for("dashboard"))


COLORS = {"violet", "coral", "mint", "sky", "sun"}

with app.app_context():
    init_db()


if __name__ == "__main__":
    app.run(debug=True)

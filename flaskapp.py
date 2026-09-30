"""
CS 5165 Intro to Cloud Computing @ University of Cincinnati.
Covers: 4a registration, 4b user details, 4c profile display,
4d re-login, 4e file upload with word count and download.
"""
import os
import secrets
import sqlite3

from flask import (Flask, abort, flash, g, redirect, render_template,
                   request, send_from_directory, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

# Absolute paths: under Apache/mod_wsgi the working directory is NOT this folder.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "users.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
SECRET_PATH = os.path.join(BASE_DIR, "secret_key.txt")
ALLOWED_EXTENSIONS = {"txt"}

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # 2 MB upload limit


def load_secret_key():
    """Keep one secret key on disk so sessions survive Apache restarts."""
    if not os.path.exists(SECRET_PATH):
        with open(SECRET_PATH, "w") as f:
            f.write(secrets.token_hex(32))
    with open(SECRET_PATH) as f:
        return f.read().strip()


app.secret_key = load_secret_key()


# ---------- Database ----------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    # all data required for the web app
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT NOT NULL UNIQUE,
            password   TEXT NOT NULL,
            firstname  TEXT NOT NULL,
            lastname   TEXT NOT NULL,
            email      TEXT NOT NULL,
            address    TEXT NOT NULL,
            filename   TEXT,
            word_count INTEGER
        )
    """)
    conn.commit()
    conn.close()


init_db()


# ---------- Helpers ----------

def allowed_file(name):
    return "." in name and name.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload(file_storage, username):
    """save the uploaded file limerick but can work for any text file; return (stored_name, word_count)."""
    stored_name = f"{username}_{secure_filename(file_storage.filename)}"
    path = os.path.join(UPLOAD_DIR, stored_name)
    file_storage.save(path)
    with open(path, encoding="utf-8", errors="replace") as f:
        word_count = len(f.read().split())
    return stored_name, word_count


def current_user():
    """ get the current user"""
    username = session.get("username")
    if not username:
        return None
    return get_db().execute(
        "SELECT * FROM users WHERE username = ?", (username,)).fetchone()


# ---------- Routes ----------

@app.route("/")
def index():
    if current_user():
        return redirect(url_for("profile"))
    return redirect(url_for("register"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html", form={})

    form = {k: request.form.get(k, "").strip() for k in
            ("username", "firstname", "lastname", "email", "address")}
    password = request.form.get("password", "")

    missing = [k for k, v in form.items() if not v]
    if missing or not password:
        flash("Fill in every field to create your account.", "error")
        return render_template("register.html", form=form), 400

    db = get_db()
    if db.execute("SELECT 1 FROM users WHERE username = ?",
                  (form["username"],)).fetchone():
        flash(f"The username \u201c{form['username']}\u201d is taken. Choose another.", "error")
        return render_template("register.html", form=form), 400

    filename, word_count = None, None
    upload = request.files.get("file")
    if upload and upload.filename:
        if not allowed_file(upload.filename):
            flash("Only .txt files can be uploaded.", "error")
            return render_template("register.html", form=form), 400
        filename, word_count = save_upload(upload, form["username"])

    db.execute(
        """INSERT INTO users
           (username, password, firstname, lastname, email, address, filename, word_count)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (form["username"], generate_password_hash(password), form["firstname"],
         form["lastname"], form["email"], form["address"], filename, word_count))
    db.commit()

    session["username"] = form["username"]
    flash("Account created.", "ok")
    return redirect(url_for("profile"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", username="")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    user = get_db().execute(
        "SELECT * FROM users WHERE username = ?", (username,)).fetchone()

    if user is None or not check_password_hash(user["password"], password):
        flash("That username and password don\u2019t match an account.", "error")
        return render_template("login.html", username=username), 401

    session["username"] = user["username"]
    return redirect(url_for("profile"))


@app.route("/profile")
def profile():
    user = current_user()
    if user is None:
        flash("Log in to see your profile.", "error")
        return redirect(url_for("login"))
    return render_template("profile.html", user=user)


@app.route("/upload", methods=["POST"])
def upload():
    user = current_user()
    if user is None:
        return redirect(url_for("login"))

    file = request.files.get("file")
    if not file or not file.filename:
        flash("Choose a file to upload.", "error")
    elif not allowed_file(file.filename):
        flash("Only .txt files can be uploaded.", "error")
    else:
        if user["filename"]:  # replace the previous upload
            old = os.path.join(UPLOAD_DIR, user["filename"])
            if os.path.exists(old):
                os.remove(old)
        filename, word_count = save_upload(file, user["username"])
        db = get_db()
        db.execute("UPDATE users SET filename = ?, word_count = ? WHERE id = ?",
                   (filename, word_count, user["id"]))
        db.commit()
        flash("File uploaded.", "ok")
    return redirect(url_for("profile"))


@app.route("/download")
def download():
    user = current_user()
    if user is None:
        return redirect(url_for("login"))
    if not user["filename"]:
        abort(404)
    # Strip the "username_" prefix so the download keeps the original name.
    original = user["filename"][len(user["username"]) + 1:]
    return send_from_directory(UPLOAD_DIR, user["filename"],
                               as_attachment=True, download_name=original)


@app.route("/logout")
def logout():
    session.clear()
    flash("You\u2019re logged out.", "ok")
    return redirect(url_for("login"))


@app.errorhandler(413)
def too_large(e):
    flash("That file is over 2 MB. Upload a smaller file.", "error")
    return redirect(request.referrer or url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)

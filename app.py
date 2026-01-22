from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "ams_secret"

# ---------------- DATABASE CONNECTION ----------------
def get_db():
    conn = sqlite3.connect("election.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- CREATE TABLES ----------------
def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        username TEXT UNIQUE,
        password TEXT,
        voted INTEGER DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        department TEXT,
        votes INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()

init_db()

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# ---------------- STUDENT SIGNUP ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO students (name, username, password) VALUES (?, ?, ?)",
                (name, username, password)
            )
            conn.commit()
        except:
            return "Username already exists"
        finally:
            conn.close()

        return redirect("/login")

    return render_template("student_signup.html")

# ---------------- STUDENT LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        student = conn.execute(
            "SELECT * FROM students WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()

        if student:
            session["student"] = student["id"]
            return redirect("/vote")

        return "Invalid login"

    return render_template("student_login.html")

# ---------------- VOTE ----------------
@app.route("/vote", methods=["GET", "POST"])
def vote():
    if "student" not in session:
        return redirect("/login")

    conn = get_db()
    student = conn.execute(
        "SELECT * FROM students WHERE id=?",
        (session["student"],)
    ).fetchone()

    if student["voted"]:
        conn.close()
        return redirect("/result")

    if request.method == "POST":
        cid = request.form["candidate"]
        conn.execute("UPDATE candidates SET votes = votes + 1 WHERE id=?", (cid,))
        conn.execute("UPDATE students SET voted = 1 WHERE id=?", (student["id"],))
        conn.commit()
        conn.close()
        return redirect("/result")

    candidates = conn.execute("SELECT * FROM candidates").fetchall()
    conn.close()

    return render_template("vote.html", candidates=candidates)

# ---------------- RESULT ----------------
@app.route("/result")
def result():
    conn = get_db()
    candidates = conn.execute("SELECT * FROM candidates").fetchall()
    conn.close()

    show_result = datetime.now().strftime("%H:%M") >= "18:00"
    return render_template("result.html", candidates=candidates, show_result=show_result)

# ---------------- ADMIN LOGIN (URL ONLY) ----------------
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form["username"] == ADMIN_USERNAME and request.form["password"] == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect("/admin/dashboard")
        return "Invalid Admin"

    return render_template("admin_login.html")

# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin/dashboard", methods=["GET", "POST"])
def admin_dashboard():
    if "admin" not in session:
        return redirect("/admin")

    conn = get_db()

    if request.method == "POST":
        conn.execute(
            "INSERT INTO candidates (name, department) VALUES (?, ?)",
            (request.form["name"], request.form["department"])
        )
        conn.commit()

    candidates = conn.execute("SELECT * FROM candidates").fetchall()
    conn.close()

    return render_template("admin_dashboard.html", candidates=candidates)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)

import csv
import io
import json
import os
import re
import secrets
import sqlite3
import time
from functools import wraps

from flask import Flask, flash, jsonify, make_response, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database import get_db, init_db, now_iso, DB_PATH
from checker import check_text
from nlp.dialect import detect_dialect
from nlp.slang import get_slang_dictionary

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "change-this-development-secret-key"
)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
if not app.config["SECRET_KEY"]:
    app.config["SECRET_KEY"] = secrets.token_hex(32)
if os.environ.get("HTTPS_ONLY", "0") == "1":
    app.config["SESSION_COOKIE_SECURE"] = True

RATE = {}
DIALECTS = ["Auto", "Kanglish", "Hinglish", "Tanglish"]


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(32)
    return session["csrf"]


app.jinja_env.globals["csrf_token"] = csrf_token


def csrf_ok():
    supplied = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
    saved = session.get("csrf", "")
    return bool(supplied and saved and secrets.compare_digest(supplied, saved))


def user():
    uid = session.get("uid")
    if not uid:
        return None
    conn = get_db()
    row = conn.execute("SELECT id,name,email,preferred_dialect,created_at FROM users WHERE id=?", (uid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not user():
            flash("Please login to access that page.", "warning")
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)
    return wrapped


def rate_limit(key, limit, window=60):
    now = time.time()
    bucket = RATE.setdefault(key, [])
    bucket[:] = [t for t in bucket if now - t < window]
    if len(bucket) >= limit:
        return False
    bucket.append(now)
    return True


@app.context_processor
def inject_globals():
    return {"me": user(), "dialects": DIALECTS}


@app.after_request
def security_headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    resp.headers["Permissions-Policy"] = "microphone=(self)"
    resp.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'"
    if os.environ.get("HTTPS_ONLY", "0") == "1":
        resp.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return resp


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/features")
def features():
    return render_template("features.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if user():
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        if not csrf_ok():
            flash("Security token expired. Please try again.", "danger")
            return redirect(url_for("register"))
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        dialect = request.form.get("preferred_dialect", "Auto")
        if not re.fullmatch(r"[A-Za-z .'-]{2,80}", name):
            flash("Enter a valid name (2-80 characters).", "danger")
        elif not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            flash("Enter a valid email address.", "danger")
        elif len(password) < 8 or not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
            flash("Password must be at least 8 characters and contain a letter and a number.", "danger")
        elif password != confirm:
            flash("Passwords do not match.", "danger")
        else:
            conn = get_db()
            try:
                cur = conn.execute(
                    "INSERT INTO users(name,email,password_hash,preferred_dialect,created_at) VALUES(?,?,?,?,?)",
                    (name, email, generate_password_hash(password), dialect if dialect in DIALECTS else "Auto", now_iso()),
                )
                conn.commit()
                session.clear()
                session["uid"] = cur.lastrowid
                csrf_token()
                flash("Account created successfully.", "success")
                return redirect(url_for("dashboard"))
            except sqlite3.IntegrityError:
                flash("That email is already registered.", "danger")
            finally:
                conn.close()
    return render_template("auth.html", mode="register")


@app.route("/login", methods=["GET", "POST"])
def login():
    if user():
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        if not csrf_ok():
            flash("Security token expired. Please try again.", "danger")
            return redirect(url_for("login"))
        ip = request.remote_addr or "unknown"
        if not rate_limit("login:" + ip, 8, 60):
            flash("Too many login attempts. Please wait one minute.", "danger")
            return redirect(url_for("login"))
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        conn = get_db()
        row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        conn.close()
        if row and check_password_hash(row["password_hash"], password):
            session.clear()
            session["uid"] = row["id"]
            csrf_token()
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("auth.html", mode="login")


@app.post("/logout")
def logout():
    if csrf_ok():
        session.clear()
        flash("You have been logged out.", "success")
    return redirect(url_for("home"))


@app.route("/dashboard")
@login_required
def dashboard():
    uid = session["uid"]
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) AS n FROM checks WHERE user_id=?", (uid,)).fetchone()["n"]
    avg = conn.execute("SELECT COALESCE(AVG(score),0) AS n FROM checks WHERE user_id=?", (uid,)).fetchone()["n"]
    slang_count = 0
    rows = conn.execute("SELECT result_json FROM checks WHERE user_id=?", (uid,)).fetchall()
    for row in rows:
        try:
            slang_count += len(json.loads(row["result_json"]).get("slang", []))
        except json.JSONDecodeError:
            pass
    recent = conn.execute("SELECT id,input_text,dialect,score,created_at FROM checks WHERE user_id=? ORDER BY id DESC LIMIT 6", (uid,)).fetchall()
    conn.close()
    return render_template("dashboard.html", total=total, avg=round(avg, 1), slang_count=slang_count, recent=[dict(r) for r in recent])


@app.route("/checker", methods=["GET", "POST"])
@login_required
def checker():
    if request.method == "POST":
        if not csrf_ok():
            flash("Security token expired. Refresh the page and try again.", "danger")
            return redirect(url_for("checker"))
        ip = request.remote_addr or "unknown"
        if not rate_limit("check:" + ip, 30, 60):
            flash("Too many checks. Please wait a moment.", "warning")
            return redirect(url_for("checker"))
        text = request.form.get("text", "").strip()
        dialect = request.form.get("dialect", "Auto")
        if not text or len(text) > 5000:
            flash("Enter between 1 and 5000 characters.", "danger")
            return redirect(url_for("checker"))
        result = check_text(text, dialect, session["uid"], DB_PATH)
        conn = get_db()
        cur = conn.execute(
            "INSERT INTO checks(user_id,input_text,dialect,result_json,score,created_at) VALUES(?,?,?,?,?,?)",
            (session["uid"], text, result["dialect"], json.dumps(result, ensure_ascii=False), result["overall_score"], now_iso()),
        )
        conn.commit()
        result["check_id"] = cur.lastrowid
        conn.close()
        return render_template("result.html", r=result)
    return render_template("checker.html", dictionary=get_slang_dictionary())


@app.route("/history")
@login_required
def history():
    conn = get_db()
    rows = conn.execute("SELECT id,input_text,dialect,score,created_at,result_json FROM checks WHERE user_id=? ORDER BY id DESC", (session["uid"],)).fetchall()
    conn.close()
    items = []
    for row in rows:
        try:
            result = json.loads(row["result_json"])
        except json.JSONDecodeError:
            result = {}
        items.append({"id": row["id"], "input_text": row["input_text"], "dialect": row["dialect"], "score": row["score"], "created_at": row["created_at"], "errors": len(result.get("errors", [])), "slang": len(result.get("slang", []))})
    return render_template("history.html", items=items)


@app.post("/history/delete/<int:check_id>")
@login_required
def delete_history(check_id):
    if not csrf_ok():
        flash("Security token expired.", "danger")
        return redirect(url_for("history"))
    conn = get_db()
    conn.execute("DELETE FROM checks WHERE id=? AND user_id=?", (check_id, session["uid"]))
    conn.commit()
    conn.close()
    flash("History item deleted.", "success")
    return redirect(url_for("history"))


@app.post("/history/clear")
@login_required
def clear_history():
    if not csrf_ok():
        return jsonify(error="CSRF validation failed"), 403
    conn = get_db()
    conn.execute("DELETE FROM checks WHERE user_id=?", (session["uid"],))
    conn.commit()
    conn.close()
    return jsonify(success=True)


@app.route("/dictionary", methods=["GET", "POST"])
@login_required
def dictionary():
    if request.method == "POST":
        if not csrf_ok():
            flash("Security token expired.", "danger")
            return redirect(url_for("dictionary"))
        word = request.form.get("word", "").strip().lower()
        meaning = request.form.get("meaning", "").strip()
        dialect = request.form.get("dialect", "Kanglish")
        if not re.fullmatch(r"[\w -]{1,50}", word) or not meaning or len(meaning) > 120:
            flash("Enter a valid word and meaning.", "danger")
        else:
            conn = get_db()
            conn.execute("INSERT OR REPLACE INTO dictionary(user_id,word,meaning,dialect,created_at) VALUES(?,?,?,?,?)", (session["uid"], word, meaning, dialect, now_iso()))
            conn.commit()
            conn.close()
            flash("Word added to your personal dictionary.", "success")
    conn = get_db()
    items = conn.execute("SELECT * FROM dictionary WHERE user_id=? ORDER BY id DESC", (session["uid"],)).fetchall()
    conn.close()
    return render_template("dictionary.html", items=[dict(x) for x in items])


@app.post("/dictionary/delete/<int:item_id>")
@login_required
def dictionary_delete(item_id):
    if not csrf_ok():
        return redirect(url_for("dictionary"))
    conn = get_db()
    conn.execute("DELETE FROM dictionary WHERE id=? AND user_id=?", (item_id, session["uid"]))
    conn.commit()
    conn.close()
    flash("Word removed.", "success")
    return redirect(url_for("dictionary"))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        if not csrf_ok():
            flash("Security token expired.", "danger")
            return redirect(url_for("profile"))
        name = request.form.get("name", "").strip()
        dialect = request.form.get("preferred_dialect", "Auto")
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        conn = get_db()
        row = conn.execute("SELECT password_hash FROM users WHERE id=?", (session["uid"],)).fetchone()
        if not re.fullmatch(r"[A-Za-z .'-]{2,80}", name):
            flash("Enter a valid name.", "danger")
        elif dialect not in DIALECTS:
            flash("Invalid dialect selection.", "danger")
        else:
            conn.execute("UPDATE users SET name=?,preferred_dialect=? WHERE id=?", (name, dialect, session["uid"]))
            if new_password:
                if len(new_password) < 8 or not re.search(r"[A-Za-z]", new_password) or not re.search(r"\d", new_password):
                    flash("New password must be at least 8 characters and contain a letter and number.", "danger")
                    conn.rollback()
                    conn.close()
                    return redirect(url_for("profile"))
                if not current_password or not check_password_hash(row["password_hash"], current_password):
                    flash("Current password is incorrect.", "danger")
                    conn.rollback()
                    conn.close()
                    return redirect(url_for("profile"))
                conn.execute("UPDATE users SET password_hash=? WHERE id=?", (generate_password_hash(new_password), session["uid"]))
            conn.commit()
            flash("Profile updated successfully.", "success")
        conn.close()
    return render_template("profile.html")


@app.route("/practice")
@login_required
def practice():
    return render_template("practice.html")


@app.post("/api/check")
@login_required
def api_check():
    if not csrf_ok():
        return jsonify(error="CSRF validation failed"), 403
    ip = request.remote_addr or "unknown"
    if not rate_limit("api:" + ip, 30, 60):
        return jsonify(error="Rate limit exceeded"), 429
    data = request.get_json(silent=True) or {}
    text = str(data.get("text", "")).strip()
    dialect = str(data.get("dialect", "Auto"))
    if not text or len(text) > 5000:
        return jsonify(error="Text must contain 1-5000 characters."), 400
    return jsonify(check_text(text, dialect, session["uid"], DB_PATH))


@app.post("/api/feedback")
@login_required
def feedback():
    if not csrf_ok():
        return jsonify(error="CSRF validation failed"), 403
    data = request.get_json(silent=True) or {}
    conn = get_db()
    conn.execute("INSERT INTO feedback(user_id,check_id,useful,created_at) VALUES(?,?,?,?)", (session["uid"], data.get("check_id"), 1 if data.get("useful") else 0, now_iso()))
    conn.commit()
    conn.close()
    return jsonify(success=True)


@app.get("/api/detect")
def api_detect():
    text = request.args.get("text", "")[:5000]
    return jsonify(detect_dialect(text))


def get_owned_check(check_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM checks WHERE id=? AND user_id=?", (check_id, session["uid"])).fetchone()
    conn.close()
    return row


@app.get("/report/<int:check_id>.csv")
@login_required
def report_csv(check_id):
    row = get_owned_check(check_id)
    if not row:
        return "Not found", 404
    result = json.loads(row["result_json"])
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["Regional Dialect AI Report"])
    writer.writerow(["Date", row["created_at"]])
    writer.writerow(["Dialect", row["dialect"]])
    writer.writerow(["Overall Score", row["score"]])
    writer.writerow(["Original", row["input_text"]])
    writer.writerow(["Correction", result.get("correction", "")])
    writer.writerow([])
    writer.writerow(["Grammar / Style Issues"])
    for issue in result.get("errors", []):
        writer.writerow([issue.get("type"), issue.get("original"), issue.get("suggestion"), issue.get("explanation")])
    writer.writerow([])
    writer.writerow(["Detected Slang"])
    for slang in result.get("slang", []):
        writer.writerow([slang.get("word"), slang.get("meaning"), slang.get("formal")])
    response = make_response(out.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = f"attachment; filename=regional_report_{check_id}.csv"
    return response


@app.get("/report/<int:check_id>.pdf")
@login_required
def report_pdf(check_id):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    from reportlab.lib import colors

    row = get_owned_check(check_id)
    if not row:
        return "Not found", 404
    result = json.loads(row["result_json"])
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15 * mm, leftMargin=15 * mm, topMargin=15 * mm, bottomMargin=15 * mm)
    styles = getSampleStyleSheet()
    safe = lambda s: str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    story = [
        Paragraph("Regional Dialect Grammar & Slang Checker", styles["Title"]),
        Spacer(1, 8),
        Paragraph(f"Dialect: {safe(row['dialect'])} | Overall score: {safe(row['score'])}% | {safe(row['created_at'])}", styles["Normal"]),
        Spacer(1, 10),
        Paragraph("Original Text", styles["Heading2"]),
        Paragraph(safe(row["input_text"]), styles["BodyText"]),
        Spacer(1, 8),
        Paragraph("Suggested Correction", styles["Heading2"]),
        Paragraph(safe(result.get("correction", "")), styles["BodyText"]),
        Spacer(1, 8),
        Paragraph("Grammar / Style Issues", styles["Heading2"]),
    ]
    data = [["Type", "Original", "Suggestion"]]
    for issue in result.get("errors", []):
        data.append([safe(issue.get("type")), safe(issue.get("original")), safe(issue.get("suggestion"))])
    if len(data) == 1:
        data.append(["None", "No major issue", "-"])
    table = Table(data, colWidths=[45 * mm, 55 * mm, 65 * mm])
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey), ("GRID", (0, 0), (-1, -1), 0.4, colors.grey), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story += [table, Spacer(1, 10), Paragraph("Detected Slang", styles["Heading2"])]
    for slang in result.get("slang", []):
        story.append(Paragraph(f"{safe(slang.get('word'))}: {safe(slang.get('meaning'))} (formal: {safe(slang.get('formal'))})", styles["BodyText"]))
    doc.build(story)
    response = make_response(buffer.getvalue())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename=regional_report_{check_id}.pdf"
    return response


@app.errorhandler(413)
def too_large(_):
    return render_template("error.html", message="The submitted content is too large."), 413


@app.errorhandler(404)
def not_found(_):
    return render_template("error.html", message="The page you requested was not found."), 404


init_db()

if __name__ == "__main__":
    import os

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
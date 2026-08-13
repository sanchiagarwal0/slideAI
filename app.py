import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, send_file, abort, send_from_directory

import storage
import db
from backend import process_file, generate_ppt_from_session_data

# static_folder="public", static_url_path="" makes local dev (`python app.py`)
# serve /css/style.css and /favicon.svg the same way Vercel's CDN serves
# public/** in production — Vercel never routes those requests to this
# Flask app at all, so this setting is purely a local-dev convenience.
app = Flask(__name__, static_folder="public", static_url_path="")
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-secret-change-me")

# Explicit static routes for Vercel. These make CSS/assets work even when
# every incoming request is routed through the Flask serverless function.
@app.route("/css/<path:filename>")
def css_file(filename):
    return send_from_directory(os.path.join(app.root_path, "public", "css"), filename)

@app.route("/favicon.svg")
def favicon_svg():
    return send_from_directory(os.path.join(app.root_path, "public"), "favicon.svg")


# Vercel Functions cap request bodies at 4.5MB — stay comfortably under that
# so large uploads fail with a clean message instead of a raw platform error.
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024  # 4MB

users = {"admin": "12345", "user1": "pass1", "user2": "pass2"}

db.init_db()


@app.route("/favicon.ico")
def favicon_ico():
    return redirect("/favicon.svg", code=307)


@app.errorhandler(413)
def too_large(_e):
    return "File too large. Please upload a file under 4MB.", 413


# ---------------- AUTH ---------------- #

@app.route("/")
def home():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    loginid = request.form.get("loginid")
    password = request.form.get("password")

    if loginid in users and users[loginid] == password:
        session["loggedin"] = True
        session["user"] = loginid
        db.log_activity(loginid, "login")
        if loginid == "admin":
            return redirect(url_for("admin"))
        return redirect(url_for("upload"))

    return "Invalid Login ID or Password!"


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/signup", methods=["POST"])
def signup():
    newid = request.form.get("newid")
    newpassword = request.form.get("newpassword")

    if newid in users:
        return "User already exists!"

    # NOTE: in-memory only, same as the original app — a fresh serverless
    # instance won't remember signups made on a different instance. Swap
    # for a real user table (see db.py) before relying on this in production.
    users[newid] = newpassword
    session["loggedin"] = True
    session["user"] = newid
    return redirect(url_for("upload"))


# ---------------- UPLOAD ---------------- #

@app.route("/upload")
def upload():
    if not session.get("loggedin"):
        return redirect(url_for("home"))
    return render_template("upload.html")


@app.route("/convert", methods=["POST"])
def convert():
    if not session.get("loggedin"):
        return redirect(url_for("home"))

    if "excelFile" not in request.files:
        return "No file uploaded!"

    file = request.files["excelFile"]
    if file.filename == "":
        return "No file selected!"

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".csv", ".xlsx", ".xls"]:
        return "Unsupported file type!"

    # Parsed, analyzed, and (charts/cleaned data/full result) uploaded to
    # blob storage entirely in-memory — nothing touches local disk, so this
    # works the same whether the function that handles /generate_ppt next
    # is this same instance or a completely different one.
    result = process_file(file)

    if not result or result.get("status") == "error":
        return f"Processing failed: {result.get('message', 'Unknown error')}"

    # Only a URL (a short string) goes in the session cookie — the full
    # analysis (insights text, chart URLs, etc.) lives in the JSON blob
    # that URL points to, so we never risk overflowing the cookie.
    session["data_blob_url"] = result["data_blob_url"]
    session["report_id"] = result["report_id"]

    return redirect(url_for("ppt"))


# ---------------- PPT PAGE ---------------- #

@app.route("/ppt")
def ppt():
    if not session.get("loggedin"):
        return redirect(url_for("home"))
    return render_template("ppt.html")


# ---------------- GENERATE PPT ---------------- #

@app.route("/generate_ppt", methods=["POST"])
def generate_ppt():
    if not session.get("loggedin"):
        return redirect(url_for("home"))

    data_blob_url = session.get("data_blob_url")
    if not data_blob_url:
        return "No processed data found!"

    try:
        data = json.loads(storage.fetch_bytes(data_blob_url))
    except Exception as e:
        return f"Could not reload processed data: {e}"

    theme = request.form.get("theme", "classic")

    try:
        ppt_bytes = generate_ppt_from_session_data(theme, data)
    except Exception as e:
        return f"PPT generation failed: {str(e)}"

    report_id = data["report_id"]
    file_name = f"report_{report_id}.pptx"
    ppt_url = storage.put_bytes(
        f"decks/{file_name}", ppt_bytes,
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )

    db.log_activity(session.get("user"), "generate_ppt", {
        "source_file": data.get("source_file"),
        "report_file": file_name,
        "theme": theme,
    })

    session["ppt_url"] = ppt_url
    session["ppt_filename"] = file_name
    session["theme"] = theme

    return redirect(url_for("preview"))


# ---------------- PREVIEW ---------------- #

@app.route("/preview")
def preview():
    if not session.get("loggedin"):
        return redirect(url_for("home"))

    data = None
    if session.get("data_blob_url"):
        try:
            data = json.loads(storage.fetch_bytes(session["data_blob_url"]))
        except Exception:
            data = None

    return render_template(
        "preview.html",
        ppt_url=session.get("ppt_url"),
        ppt_filename=session.get("ppt_filename"),
        data=data,
        theme=session.get("theme"),
    )


# ---------------- DOWNLOAD (local-dev fallback only) ---------------- #
# In production, ppt_url / chart URLs are public Vercel Blob URLs and the
# templates link straight to them. This route only matters when running
# locally without BLOB_READ_WRITE_TOKEN set, where storage.py writes to
# ./local_blob_store instead and returns /local-blob/<name> URLs.

@app.route("/local-blob/<path:name>")
def local_blob(name):
    if storage.USE_VERCEL_BLOB:
        abort(404)
    full_path = os.path.join(storage.LOCAL_STORE_DIR, name)
    if not os.path.isfile(full_path):
        abort(404)
    return send_file(full_path)


# ---------------- ADMIN ---------------- #

@app.route("/admin")
def admin():
    if not session.get("loggedin") or session.get("user") != "admin":
        return "Access denied! Admin only."

    logins, generations = db.fetch_logs()
    return render_template("admin.html", logins=logins, generations=generations)


# ---------------- RUN ---------------- #

if __name__ == "__main__":
    app.run(debug=True)

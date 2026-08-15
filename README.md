# SlideAI

Turn a spreadsheet into a polished PowerPoint presentation — automatically.

**🔗 Live demo:** https://slideai-lilac.vercel.app/

---

## Table of Contents

- [What is SlideAI?](#what-is-slideai)
- [How It Works](#how-it-works)
- [Features](#features)
- [Try the Live Demo](#try-the-live-demo)
- [Running It Locally](#running-it-locally)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Deploying Your Own Copy](#deploying-your-own-copy)
- [Limitations](#limitations)
- [FAQ](#faq)

---

## What is SlideAI?

SlideAI is a web app that takes a plain data file (like a CSV or Excel spreadsheet) and turns
it into a ready-to-use PowerPoint presentation — complete with charts, key numbers, and written
insights about your data.

Instead of spending hours building slides by hand, you upload your file, pick a look you like,
and SlideAI does the analysis and slide-building for you.

## How It Works

1. **Upload** — Drop in a `.csv` or `.xlsx` file.
2. **Choose a theme** — Pick the visual style you want your deck to have.
3. **Automatic analysis** — SlideAI scans your data for:
   - Key numbers (KPIs)
   - Trends over time
   - Unusual values (outliers)
   - Relationships between columns (correlations)
4. **Get your deck** — Download a finished `.pptx` file with charts and explanations already
   built in.

## Features

- 📊 Works with CSV and Excel files
- 🎨 Multiple slide themes to choose from
- 🤖 Automatic data analysis — no formulas or charting needed on your end
- 📥 Download a real, editable PowerPoint file
- 🔐 Simple login system (demo accounts included)
- 🖥️ Admin view to see activity/usage

## Try the Live Demo

Go to **https://slideai-lilac.vercel.app/** and log in with any of these demo accounts:

| Username | Password |
|----------|----------|
| `admin`  | `12345`  |
| `user1`  | `pass1`  |
| `user2`  | `pass2`  |

Then upload a spreadsheet and follow the on-screen steps.

> Note: this is a demo — please don't upload real personal or sensitive data.

## Running It Locally

Want to run SlideAI on your own computer instead of using the live version?

**Requirements:** Python installed on your machine.

```bash
# 1. Install the required packages
pip install -r requirements.txt

# 2. (Optional) copy the example settings file
cp .env.example .env

# 3. Start the app
python app.py
```

Now open your browser to:

```
http://127.0.0.1:5000
```

Log in with `admin / 12345` and try it out.

## Project Structure

A quick tour of the important files:

```
slideai/
├── app.py              # Main application — routes/pages
├── backend.py           # Reads and analyzes your uploaded file
├── storage.py           # Handles saving files/charts
├── db.py                # Handles activity logging
├── templates/            # The web pages (HTML)
├── public/               # Images, styles, static files
└── requirements.txt       # List of Python packages needed
```

## Tech Stack

- **Backend:** Python (Flask)
- **Data analysis:** pandas
- **Charts:** matplotlib
- **Slide generation:** python-pptx
- **Frontend:** Plain HTML, CSS, and JavaScript
- **Hosting:** Vercel

## Deploying Your Own Copy

If you'd like to host your own version on Vercel:

1. Push this project to a GitHub repository.
2. Import it into [Vercel](https://vercel.com) — it auto-detects the app, no extra config needed.
3. In your Vercel project, go to **Storage → Create Database → Blob** (used to store
   generated files).
4. *(Optional)* Also create a **Postgres** database if you want activity logging.
5. Go to **Settings → Environment Variables** and add a `SECRET_KEY` (any long random text).
6. Redeploy — you're live!

## Limitations

- 📁 Uploaded files must be **under 4MB**.
- 👤 Signups made through the app aren't permanently saved — this is a demo login system, not a
  real user database.
- ⏳ The very first request after the app has been idle for a while may load a bit slowly — this
  is normal and just how this type of free hosting works.

## FAQ

**Do I need to install anything to try it?**
No — just visit the live demo link and log in with a demo account.

**What file types can I upload?**
CSV (`.csv`) or Excel (`.xlsx`) files.

**Can I edit the PowerPoint after it's generated?**
Yes! It downloads as a normal `.pptx` file you can open and edit in PowerPoint, Google Slides,
Keynote, etc.

**Is my data safe?**
This is a demo project, so avoid uploading anything private or sensitive.

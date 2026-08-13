# SlideAI (Vercel-ready)

Upload a CSV or Excel file, pick a theme, and SlideAI analyzes your data — KPIs, trends,
outliers, correlations — into a polished PowerPoint deck. Same Flask app and vanilla
HTML/CSS/JS frontend as before, rearchitected so it actually works once deployed to Vercel's
serverless functions, not just locally.

## Why the previous version wouldn't have worked on Vercel

The original Flask app saved uploads to local disk, wrote generated `.pptx`/chart files to
`static/reports/` and `static/charts/`, and logged activity to a local SQLite file — then read
several of those back in a *later* request. Vercel Functions don't share a persistent
filesystem between invocations, so that flow would deploy successfully and then break the
first time someone actually generated a deck. This version fixes that:

| Problem | Fix |
|---|---|
| Upload saved to local disk, reloaded in a later request | Parsed entirely in-memory in the same request (`backend.py: load_file_from_upload`) |
| Chart PNGs + generated `.pptx` written to local disk | Generated in-memory, uploaded to **Vercel Blob**, referenced by URL (`storage.py`) |
| `activity_log.db` (local SQLite) | Logged to **Postgres** via `DATABASE_URL` when set (`db.py`) |
| Static assets served via Flask's `static_folder` | Moved to `public/`, per [Vercel's Flask guidance](https://vercel.com/docs/frameworks/backend/flask) — served from Vercel's CDN, never hits the Python function |
| Session held the full analysis (KPIs, insight text, chart paths) | Session now holds only a **URL** to one JSON blob containing all of that — keeps the cookie tiny regardless of dataset size |

**Local development still works with zero cloud setup** — `storage.py` and `db.py` fall back to
a local folder (`local_blob_store/`) and local SQLite when `BLOB_READ_WRITE_TOKEN` /
`DATABASE_URL` aren't set, so `python app.py` behaves the same as before.

## Deploying to Vercel

1. **Push this to a Git repo** and import it in Vercel (or `vercel deploy` from the CLI).
   Vercel auto-detects the Flask entrypoint (`app.py`) — no build config needed for that part.

2. **Create a Blob store**: Project → Storage → Create Database → **Blob** → connect it to this
   project. This sets `BLOB_READ_WRITE_TOKEN` automatically.

3. **Create a Postgres database** (optional, only needed for the admin activity log): Project →
   Storage → Create Database → **Postgres** (Neon-backed). This sets `DATABASE_URL`
   automatically. Skip this and the app still works fine — activity logging just no-ops.

4. **Set `SECRET_KEY`**: Project → Settings → Environment Variables → add a long random string.

5. Redeploy after adding the integrations so the new environment variables take effect.

## Known platform limits to plan around

- **4MB upload cap.** Vercel Functions cap request bodies at 4.5MB; `app.py` enforces a 4MB
  limit itself so oversized uploads fail with a clean message instead of a raw platform error.
  If you need larger files, that means moving to Vercel Blob's client-side upload flow (browser
  uploads directly to Blob, bypassing the function) — a real change, not a config tweak.
- **`vercel_blob` is an unofficial, community-maintained PyPI package** — there's no official
  Vercel Python SDK for Blob at the time of writing. It's a thin wrapper around the same REST
  API the official JS SDK uses. Worth a quick smoke test after your first deploy (upload a file,
  confirm it shows up in the Blob store dashboard) since I couldn't test it against real Vercel
  credentials from where this was built.
- **In-memory user store.** Signups (`/signup`) still only live in the running function
  instance's memory, same as the original app — fine for the demo logins (`admin/12345`,
  `user1/pass1`, `user2/pass2`), not for real accounts. Move to a Postgres users table with
  hashed passwords before treating this as a real login system.
- **Cold starts.** pandas + matplotlib + python-pptx is a moderately heavy dependency stack;
  expect a slower first request after idle periods.

## Local development

```bash
pip install -r requirements.txt
cp .env.example .env   # optional locally — everything falls back gracefully without it
python app.py
```

Open `http://127.0.0.1:5000`. Demo login: `admin/12345`.

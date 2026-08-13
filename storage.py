"""
Storage abstraction so the app doesn't depend on a persistent local
filesystem — which Vercel's serverless functions don't provide between
requests.

- If BLOB_READ_WRITE_TOKEN is set (i.e. a Vercel Blob store is connected),
  files are uploaded to Vercel Blob and referenced by their public URL.
- Otherwise (local development), files are written under ./local_blob_store
  and served back via the /local-blob/<path> route registered in app.py.

Either way, callers get back a URL they can store (in the session, or embed
in HTML) and later fetch bytes from with `fetch_bytes()`.
"""

import os
import uuid
import requests

LOCAL_STORE_DIR = "local_blob_store"
USE_VERCEL_BLOB = bool(os.environ.get("BLOB_READ_WRITE_TOKEN"))

if USE_VERCEL_BLOB:
    import vercel_blob


def _unique_pathname(pathname: str) -> str:
    stem, ext = os.path.splitext(pathname)
    return f"{stem}_{uuid.uuid4().hex[:10]}{ext}"


def put_bytes(pathname: str, data: bytes, content_type: str | None = None) -> str:
    """Upload bytes and return a URL that can be fetched later (possibly from
    a different serverless invocation)."""
    if USE_VERCEL_BLOB:
        options = {"addRandomSuffix": "true"}
        if content_type:
            options["contentType"] = content_type
        resp = vercel_blob.put(pathname, data, options)
        return resp["url"]

    # Local dev fallback
    os.makedirs(LOCAL_STORE_DIR, exist_ok=True)
    unique_name = _unique_pathname(pathname)
    full_path = os.path.join(LOCAL_STORE_DIR, unique_name)
    os.makedirs(os.path.dirname(full_path) or ".", exist_ok=True)
    with open(full_path, "wb") as f:
        f.write(data)
    return f"/local-blob/{unique_name}"


def fetch_bytes(url: str) -> bytes:
    """Fetch bytes back from a URL previously returned by put_bytes()."""
    if url.startswith("/local-blob/"):
        full_path = os.path.join(LOCAL_STORE_DIR, url[len("/local-blob/"):])
        with open(full_path, "rb") as f:
            return f.read()

    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.content

# SlideAI — Vercel Deployment

## Deploy

1. Upload this project to GitHub.
2. Import the repository into Vercel.
3. Vercel will use `vercel.json` and `app.py` as the Python serverless entry point.
4. Add all required secrets/environment variables from `.env.example` in:
   **Vercel → Project → Settings → Environment Variables**
5. Redeploy after adding environment variables.

## Important

Vercel serverless functions have ephemeral local storage. If SlideAI writes uploaded/generated
files to the local filesystem and expects them to persist between requests, use external storage
for production (for example, object storage or a database).

Do not commit `.env` or API keys to GitHub.


## Static files fix
The deployment uses `api/index.py` as the Vercel entry point and explicit Flask routes for `/css/*` and `/favicon.svg`, so the existing `public/` assets are available in serverless deployment.

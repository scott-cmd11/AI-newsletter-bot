# Vercel Deployment Guide

## Overview

This guide explains how to deploy the AI Newsletter Bot to Vercel.

**Note:** Vercel is designed for serverless functions, which has some limitations:
- File storage doesn't persist between cold starts (functions restart periodically)
- Reviews/newsletters exist only during a single session
- For persistent storage, see "Storage Options" below

## Quick Start

### 1. Push to GitHub

Ensure your code is pushed to GitHub:
```bash
git add .
git commit -m "Prepare for Vercel deployment"
git push origin main
```

### 2. Connect to Vercel

1. Go to https://vercel.com
2. Click "Add New..." → "Project"
3. Import your GitHub repository
4. Vercel auto-detects Python project
5. Click "Deploy"

### 3. Set Environment Variables

After creating the project, go to **Settings** → **Environment Variables** and add:

```
AUTH_PASSWORD=your_secure_password_here
GEMINI_API_KEY=your_gemini_key
```

Optional:
```
LOG_LEVEL=INFO
CACHE_TTL=1800
```

### 4. Deploy

Vercel automatically deploys on every GitHub push.

## Storage Options

### Option A: Vercel KV (Redis-like storage)
Recommended for production use.

1. Go to Vercel dashboard → **Storage** → **Create Database**
2. Choose **KV Store**
3. Add to project
4. Environment variables auto-populate

Then use the KV client in your app (requires code modification).

### Option B: Supabase (Free PostgreSQL)

1. Create account at https://supabase.com
2. Create new project
3. Get connection string
4. Add to Vercel environment variables

### Option C: In-Memory Cache (No Persistence)

Works as-is with no setup. Reviews/newsletters don't persist between cold starts.

**Best for:** Testing, development

**Note:** Every cold start (usually after 15 min inactivity) resets all data

## How It Works on Vercel

1. **First Request:** App initializes, reads from `/tmp` directory
2. **Subsequent Requests:** Data accessible within same "warm" instance
3. **Cold Start:** After inactivity, app reinitializes (fresh state)

For typical usage:
- ✅ Fetch articles (works)
- ✅ Select articles (works within session)
- ✅ Generate newsletter (works)
- ⚠️ Data disappears after cold start (app restarts)

## Limitations vs Render

| Feature | Vercel | Render |
|---------|--------|--------|
| **Cold starts** | Yes (~2-5s) | No (always warm) |
| **File persistence** | No (except during session) | Yes (persistent) |
| **Free tier** | 100 GB-hours/month | Limited |
| **Performance** | Good (CDN-optimized) | Good (traditional) |

## Troubleshooting

### App won't deploy
Check Vercel logs:
1. Go to Vercel dashboard
2. Click your project
3. Go to "Deployments" tab
4. Click most recent deployment
5. Scroll to "Logs" section

### Reviews disappearing
This is normal on Vercel - data doesn't persist between cold starts.
**Solution:** Use Vercel KV or Supabase for persistent storage.

### Auth not working
Verify `AUTH_PASSWORD` environment variable is set in Vercel.

### Personalization not working
First fetch analyzes reviews (may take 5-10s on first cold start).

## Going Back to Render

To switch back to Render:

1. Go to https://render.com
2. Create new service
3. Connect GitHub repo
4. Set environment variables
5. Deploy

Render has better file persistence for this use case.

## Best Practices

1. **Keep dependencies small** - Reduces cold start time
2. **Set AUTH_PASSWORD** - Secure your deployment
3. **Monitor Vercel logs** - For debugging issues
4. **Use KV store** - For production data persistence

## Performance Tips

- First request (cold start): ~5-10 seconds
- Subsequent requests: <1 second
- Full fetch + generate: ~15-20 seconds
- Personalization: ~2-3 seconds on first use

## Support

For Vercel-specific issues, see: https://vercel.com/docs/platforms/v0-runtime

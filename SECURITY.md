# Security Guidelines

## API Key Safety ✅

Your GEMINI_API_KEY is **secure** in this codebase:

### What We Do RIGHT
- ✅ Keys retrieved via `os.environ.get()` (safe method)
- ✅ Keys **NEVER logged** or printed to console
- ✅ Keys **NEVER returned** in API responses
- ✅ Keys **NEVER stored** in code
- ✅ Keys passed directly to Google API (no intermediate storage)
- ✅ No error messages expose key values

### Example: Safe Usage
```python
# ✅ SAFE: Retrieved from environment, never logged
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    logger.error("GEMINI_API_KEY not set in environment")  # ✅ Doesn't log the key
    return False

genai.configure(api_key=api_key)  # ✅ Passed directly to library
```

### Example: UNSAFE (Not in our code)
```python
# ❌ UNSAFE: Would expose key
logger.info(f"Using API key: {api_key}")
return {"api_key": api_key}  # ❌ Never do this
print(f"Key is: {api_key}")  # ❌ Never do this
```

## Adding Your API Key to Vercel

When adding `GEMINI_API_KEY` to Vercel:

### ✅ DO THIS (Safe)
1. Go to Vercel Dashboard
2. Project Settings → Environment Variables
3. Add:
   - **Name:** `GEMINI_API_KEY`
   - **Value:** `gsk_xxx...` (your actual key)
4. Click Save
5. Vercel **never exposes** environment variables in logs or responses

### ❌ DON'T DO THIS
- ❌ Never commit your API key to GitHub
- ❌ Never add to `.env` file that's committed
- ❌ Never put in code comments
- ❌ Never paste in issue descriptions
- ❌ Never use the same key in multiple projects

## Vercel Security Features

Vercel environment variables are:
- ✅ Encrypted at rest
- ✅ Encrypted in transit
- ✅ Never logged to build output
- ✅ Never visible in public URLs
- ✅ Only accessible to your deployment

## Password Protection

Your `AUTH_PASSWORD` is:
- ✅ Checked against incoming requests (HTTP Basic Auth)
- ✅ Never stored as plain text
- ✅ Never logged (removed from health endpoint)
- ✅ Only needed to access /fetch, /save, /generate routes

### If Password Leaked
If someone gets your password:
1. Go to Vercel Dashboard
2. Change `AUTH_PASSWORD` value
3. Redeploy (auto-deploys)
4. Old password no longer works

## What's Sent to Google

Only safe data is sent to Gemini API:
- ✅ Article titles
- ✅ Article summaries
- ✅ Article sources
- ✅ Request: "Create a newsletter from these articles"

Never sent:
- ❌ Passwords
- ❌ Authentication tokens
- ❌ Personal data
- ❌ Logs or debug info

## Monitoring Your API Usage

Monitor your Gemini API usage at:
https://makersuite.google.com/app/apikey

If you notice unusual activity:
1. Go to Google AI Studio
2. Regenerate your API key
3. Update Vercel environment variable
4. Redeploy

## Data Privacy

Your newsletter data:
- ✅ Stored locally in `/tmp` on Vercel (session-only)
- ✅ Not sent to external services (except Gemini for summarization)
- ✅ Not stored permanently unless using Vercel KV
- ✅ Auto-deleted after function completes

## Regular Security Checks

Recommended:
- Check Vercel environment variables quarterly
- Rotate API keys annually
- Monitor Google API usage for anomalies
- Keep dependencies updated

## Questions?

If you have security concerns:
1. Don't expose secrets in GitHub issues
2. Check this file first
3. Test locally before deploying
4. Use Vercel's environment variable preview feature to test

---

**Bottom Line:** Your code is secure. The API key will be safe on Vercel. 🔒

## Security Headers ✅

The application includes standard security headers to protect users:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: SAMEORIGIN`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy` (configured for current architecture)

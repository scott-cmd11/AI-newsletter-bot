# Sentinel's Security Journal 🛡️

## 2026-02-14 - [Missing CSRF Protection]
**Vulnerability:** The Flask application in `src/web.py` lacked Cross-Site Request Forgery (CSRF) protection on POST endpoints like `/save`. An attacker could potentially trick an authenticated user into modifying their article selection via a malicious site.
**Learning:** Existing memory indicated CSRF protection was present in a template (`KANBAN_TEMPLATE`), but it was absent from the main deployed application (`src/web.py`) and its template (`web_interface.html`). Do not rely on memory or secondary apps (`curator_app.py`) to assume security of the main deployment.
**Prevention:** Implemented a manual Synchronizer Token pattern in `src/web.py` using `secrets` and `session`. Added a global `csrf_token` function for templates and a `before_request` hook to validate tokens on all POST requests. Updated `web_interface.html` to include the token.

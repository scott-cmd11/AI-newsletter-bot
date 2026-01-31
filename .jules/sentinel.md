# Sentinel's Security Journal

## 2025-02-19 - [Manual CSRF Protection Pattern]
**Vulnerability:** The Flask application accepted POST requests (specifically `/save`) without any Anti-CSRF token verification. This allowed Cross-Site Request Forgery attacks where a malicious site could force an authenticated user to change their article selections without their knowledge.
**Learning:** In environments where adding new dependencies (like `Flask-WTF`) is restricted or discouraged, critical security features like CSRF protection can be implemented manually using Python's standard `secrets` library and Flask's `session`. The pattern involves:
1. Generating a token with `secrets.token_hex()` and storing it in `session`.
2. Injecting it into templates via `app.jinja_env.globals`.
3. Validating it in a `before_request` hook using `secrets.compare_digest()` against `request.form`, `request.json`, or headers.
**Prevention:** Enforce CSRF validation globally for all state-changing methods (POST, PUT, DELETE, etc.) using a middleware or `before_request` hook, rather than relying on individual route decorators which are easily missed.
